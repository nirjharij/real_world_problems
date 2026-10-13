import anthropic
import json
import logging
import os
import uvicorn

from anthropic import AsyncAnthropic
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request, Header, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger("llm_stream")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "16000"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = AsyncAnthropic(timeout=120.0, max_retries=2)
    yield
    await app.state.client.close()

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)

# async def verify_api_key(x_api_key: str = Header(...)):
#     # Replace with real auth (JWT/OAuth) + per-user rate limiting
#     if x_api_key != os.environ["SERVICE_API_KEY"]:
#         raise HTTPException(status_code=401, detail="Unauthorized")

# @app.post("/llm-response", dependencies=[Depends(verify_api_key)])
@app.post("/llm-response")
async def llm_response(body: ChatRequest,  request: Request):
    client: AsyncAnthropic = request.app.state.client
    async def gen():
        try:
            async with app.state.client.messages.stream(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": body.prompt}],
            ) as s:
                async for text in s.text_stream:
                    yield {"data": json.dumps({"token": text})}
                final = await s.get_final_message()

            logger.info("stream complete id=%s stop=%s out_tokens=%s",
                        final.id, final.stop_reason, final.usage.output_tokens)
            yield {"event": "done", "data": "[DONE]"}

        except anthropic.RateLimitError:
            logger.warning("rate limited")
            yield {"event": "error", "data": json.dumps({"code": "rate_limited"})}
        except anthropic.APIStatusError as e:
            logger.error("upstream status=%s", e.status_code)
            yield {"event": "error", "data": json.dumps({"code": "upstream_error"})}
        except anthropic.APIConnectionError:
            logger.error("upstream connection failed")
            yield {"event": "error", "data": json.dumps({"code": "upstream_unavailable"})}

    return EventSourceResponse(gen(), ping=15)  # sends a keep-alive every 15s


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)