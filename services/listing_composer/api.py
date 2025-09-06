from fastapi import FastAPI, HTTPException
from .service import DraftPayload, save_draft, get_draft
from ..common.logger import init_logger, logging_middleware
from ..common.monitoring import init_monitoring

init_logger()
app = FastAPI()
app.middleware("http")(logging_middleware)
init_monitoring(app)


@app.post("/drafts", response_model=DraftPayload)
async def create_draft(payload: DraftPayload):
    draft = await save_draft(payload)
    return DraftPayload(**draft.dict())


@app.get("/drafts/{draft_id}", response_model=DraftPayload)
async def read_draft(draft_id: int):
    draft = await get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft not found")
    return DraftPayload(**draft.dict())
