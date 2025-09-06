import json
from services.bulk_create.service import (
    parse_products_from_csv,
    parse_products_from_json,
)


def test_parse_products_from_csv():
    variants = json.dumps([{ "sku": "s1", "price": 9.99 }])
    images = json.dumps(["http://example.com/img.png"])
    import io, csv as csvmod

    output = io.StringIO()
    writer = csvmod.writer(output)
    writer.writerow(["title", "description", "price", "category", "variants", "image_urls"])
    writer.writerow(["Shirt", "Desc", 9.99, "apparel", variants, images])
    writer.writerow(["", "Bad", 9.99, "apparel", variants, images])
    csv_content = output.getvalue()
    items, errors = parse_products_from_csv(csv_content)
    assert len(items) == 1
    assert items[0].title == "Shirt"
    assert len(errors) == 1


def test_parse_products_from_json():
    data = [
        {
            "title": "Shirt",
            "description": "Desc",
            "price": 9.99,
            "category": "apparel",
            "variants": [{"sku": "s1", "price": 9.99}],
            "image_urls": ["http://example.com/img.png"],
        },
        {
            "title": "",
            "description": "Bad",
            "price": -1,
            "category": "apparel",
            "variants": [],
            "image_urls": [],
        },
    ]
    items, errors = parse_products_from_json(json.dumps(data))
    assert len(items) == 1
    assert len(errors) == 1
