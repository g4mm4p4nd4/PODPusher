from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


def create_sku(idea: str) -> dict:
    """Create a stub SKU dictionary."""
    return {"product_id": "prod-123", "variant_id": "var-123", "idea": idea}


def publish_listing(sku: dict) -> dict:
    """Return a stub listing dictionary."""
    return {
        "product_id": sku.get("product_id"),
        "variant_id": sku.get("variant_id"),
        "listing_url": "https://example.com/listing/123",
    }


class IdeaIn(BaseModel):
    idea: str


@app.post("/create-sku")
async def create_sku_endpoint(payload: IdeaIn) -> dict:
    """API endpoint for creating a SKU."""
    return {"product": create_sku(payload.idea)}


class SKUIn(BaseModel):
    product_id: str
    variant_id: str


@app.post("/publish-listing")
async def publish_listing_endpoint(payload: SKUIn) -> dict:
    """API endpoint for publishing a listing."""
    return {"listing": publish_listing(payload.model_dump())}
