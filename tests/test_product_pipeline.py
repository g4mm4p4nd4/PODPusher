from services.common.product_pipeline import assemble_products


def test_assemble_products_matches_gateway_shape() -> None:
    ideas = [
        {
            "id": 11,
            "term": "cats",
            "category": "animals",
            "description": "Cat mug with floral outline",
            "suggested_price": 29.5,
        }
    ]
    images = [
        {
            "id": 21,
            "idea_id": 11,
            "image_url": "https://example.com/cat-mug.png",
            "category": "animals",
        }
    ]

    assert assemble_products(ideas, images) == [
        {
            "id": 21,
            "idea_id": 11,
            "title": "Cat mug with floral outline",
            "description": "Cat mug with floral outline",
            "image_url": "https://example.com/cat-mug.png",
            "category": "animals",
            "tags": ["animals", "cats"],
            "price": 29.5,
        }
    ]
