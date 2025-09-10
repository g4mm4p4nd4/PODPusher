from fastapi import FastAPI

from .workers import start, stop

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    await start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await stop()
