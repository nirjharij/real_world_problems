# Real World Production ready problems for Interviews in Python

This repo contains real-world coding problems with production-ready code. Each one is something you'd actually build on the job, which makes it useful practice for coding and system design interviews.

## Problems

| Problem | File | Description |
|---|---|---|
| LLM output streaming | `llm_output_stream.py` | FastAPI endpoint that streams Claude's response token by token over Server-Sent Events, with keep-alive pings and a done event. |

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
export ANTHROPIC_API_KEY=...   # or put it in .env
```
