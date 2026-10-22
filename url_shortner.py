import hashlib
import logging
import string
import uvicorn

from fastapi import FastAPI, Body, Path
from fastapi.responses import JSONResponse
from pydantic import HttpUrl
from typing import Annotated

from starlette.responses import RedirectResponse

logger = logging.getLogger("url_shortner")
app = FastAPI()

COUNTER = 0

BASE_URL = "http://example.com/"
ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase  # "0-9A-Za-z"
BASE = len(ALPHABET)  # 62

short_to_long = {}
long_to_short = {}

def base62_encode(n: int, length: int = 6) -> str:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return ALPHABET[0]
    chars = []
    while n > 0:
        n, r = divmod(n, BASE)     # divmod returns (quotient, remainder)
        chars.append(ALPHABET[r])
    code = "".join(reversed(chars))
    if len(code) > length:
        raise ValueError(f"{n} doesn't fit in {length} characters")
    return code.rjust(length, ALPHABET[0])   # 12345 → "0003D7"

@app.post("/urls")
async def shorten_url(url: Annotated[HttpUrl, Body(embed=True)]):
    long_url = str(url)
    long_url_hash = hashlib.sha256(long_url.encode()).digest()
    if long_url_hash in long_to_short:
        short_url = long_to_short[long_url_hash]
        content = {"short_url": BASE_URL + short_url}
        logger.info(f"Shortened URL for {long_url} already exists and is {short_url}")
        return JSONResponse(status_code=200, content=content)

    global COUNTER
    COUNTER += 1
    try:
        code = base62_encode(COUNTER)
    except ValueError:
        logger.exception("Failed to encode base62 code for value %s", COUNTER)
        return JSONResponse(status_code=500, content={"message": "Failed to create a short Url. Try again"})
    short_to_long[code] = long_url
    long_to_short[long_url_hash] = code
    short_url = BASE_URL + str(code)
    content = {"short_url": short_url}
    logger.info(f"Created shortened URL for {long_url} : {short_url}")
    return JSONResponse(status_code=201, content=content)

@app.get("/urls/{code}")
async def fetch_url(code: Annotated[str, Path(pattern=r"^[A-Za-z0-9]{6}$")]):
    if code in short_to_long:
        return RedirectResponse(url=short_to_long[code], status_code=301)
    return JSONResponse(status_code=404, content={"message": "URL not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)