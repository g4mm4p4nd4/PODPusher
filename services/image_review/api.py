from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from ..logging import get_logger
from ..monitoring import setup_monitoring
from .service import list_products, update_product
from ..common.localization import get_message

app = FastAPI()
_logger = get_logger(__name__)
setup_monitoring(app, "image_review")


class UpdatePayload(BaseModel):
    rating: int | None = None
    tags: list[str] | None = None
    flagged: bool | None = None


@app.get("/")
async def get_products():
    return await list_products()


@app.post("/{product_id}")
async def update_product_endpoint(
    request: Request, product_id: int, payload: UpdatePayload
):
    product = await update_product(
        product_id,
        rating=payload.rating,
        tags=payload.tags,
        flagged=payload.flagged,
    )
    if not product:
        lang = request.headers.get('Accept-Language', 'en')
        msg = get_message(lang, 'product_not_found')
        raise HTTPException(status_code=404, detail=msg)
    return product
