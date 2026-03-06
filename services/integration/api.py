from fastapi import Depends, FastAPI
from pydantic import BaseModel

from services.common.auth import require_user_id
from services.models import OAuthProvider

from .service import create_sku, load_oauth_credentials, publish_listing


app = FastAPI()


class ProductList(BaseModel):
    products: list[dict]


@app.post("/sku")
async def sku(
    data: ProductList,
    user_id: int = Depends(require_user_id),
):
    credential = await load_oauth_credentials(user_id, OAuthProvider.PRINTIFY)
    return create_sku(data.products, credential=credential)


@app.post("/listing")
async def listing(
    product: dict,
    user_id: int = Depends(require_user_id),
):
    credential = await load_oauth_credentials(user_id, OAuthProvider.ETSY)
    return publish_listing(product, credential=credential)


@app.post("/create-sku")
async def create_sku_legacy(
    data: ProductList,
    user_id: int = Depends(require_user_id),
):
    """Legacy endpoint for backward compatibility."""
    credential = await load_oauth_credentials(user_id, OAuthProvider.PRINTIFY)
    products = create_sku(data.products, credential=credential)
    return {"product": products}


@app.post("/publish-listing")
async def publish_listing_legacy(
    product: dict,
    user_id: int = Depends(require_user_id),
):
    """Legacy endpoint for backward compatibility."""
    credential = await load_oauth_credentials(user_id, OAuthProvider.ETSY)
    listing = publish_listing(product, credential=credential)
    return {"listing": listing.get("etsy_url"), "product": listing}
