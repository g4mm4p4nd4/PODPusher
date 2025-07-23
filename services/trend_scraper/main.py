from fastapi import FastAPI

app = FastAPI()


def fetch_trends() -> list[str]:
    """Return a static list of trending hashtags."""
    return ["#yoga", "#coffee", "#cats", "#gaming"]


@app.get("/trends")
async def get_trends() -> dict[str, list[str]]:
    """Endpoint returning trending hashtags."""
    return {"trends": fetch_trends()}
