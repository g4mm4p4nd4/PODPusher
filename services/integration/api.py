from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from services.common.auth import require_user_id
from services.common.observability import register_observability
from services.models import OAuthProvider

from .service import (
    IntegrationServiceError,
    create_printify_product,
    create_sku,
    load_oauth_credentials,
    publish_listing,
)


app = FastAPI()
register_observability(app, service_name="integration")


class ProductList(BaseModel):
    products: list[dict]


class ProductCreate(BaseModel):
    idea_id: str
    image_ids: list[str]
    blueprint_id: str
    variants: list[str]


def _map_integration_error(exc: IntegrationServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@app.post("/sku")
async def sku(
    data: ProductList,
    user_id: int = Depends(require_user_id),
):
    credential = await load_oauth_credentials(user_id, OAuthProvider.PRINTIFY)
    try:
        return create_sku(data.products, credential=credential, require_live=True)
    except IntegrationServiceError as exc:
        raise _map_integration_error(exc) from exc


@app.post("/listing")
async def listing(
    product: dict,
    user_id: int = Depends(require_user_id),
):
    credential = await load_oauth_credentials(user_id, OAuthProvider.ETSY)
    try:
        return publish_listing(product, credential=credential, require_live=True)
    except IntegrationServiceError as exc:
        raise _map_integration_error(exc) from exc


@app.post("/create-sku")
async def create_sku_legacy(
    data: ProductList,
    user_id: int = Depends(require_user_id),
):
    """Legacy endpoint for backward compatibility."""
    credential = await load_oauth_credentials(user_id, OAuthProvider.PRINTIFY)
    try:
        products = create_sku(data.products, credential=credential, require_live=True)
    except IntegrationServiceError as exc:
        raise _map_integration_error(exc) from exc
    return {"product": products}


@app.post("/publish-listing")
async def publish_listing_legacy(
    product: dict,
    user_id: int = Depends(require_user_id),
):
    """Legacy endpoint for backward compatibility."""
    credential = await load_oauth_credentials(user_id, OAuthProvider.ETSY)
    try:
        listing = publish_listing(product, credential=credential, require_live=True)
    except IntegrationServiceError as exc:
        raise _map_integration_error(exc) from exc
    return {"listing": listing.get("etsy_url"), "product": listing}


@app.post("/api/printify/products/create")
async def create_printify_product_endpoint(
    data: ProductCreate,
    user_id: int = Depends(require_user_id),
):
    credential = await load_oauth_credentials(user_id, OAuthProvider.PRINTIFY)
    try:
        return create_printify_product(
            data.idea_id,
            data.image_ids,
            data.blueprint_id,
            data.variants,
            credential=credential,
            require_live=True,
        )
    except IntegrationServiceError as exc:
        raise _map_integration_error(exc) from exc


@app.post("/api/etsy/listings/publish")
async def publish_listing_endpoint(
    product: dict,
    user_id: int = Depends(require_user_id),
):
    credential = await load_oauth_credentials(user_id, OAuthProvider.ETSY)
    try:
        return publish_listing(product, credential=credential, require_live=True)
    except IntegrationServiceError as exc:
        raise _map_integration_error(exc) from exc
