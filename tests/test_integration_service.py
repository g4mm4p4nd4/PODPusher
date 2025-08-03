from services.integration import service


def test_create_sku_returns_stub_when_no_api_key(monkeypatch):
    monkeypatch.setattr(service, "PRINTIFY_API_KEY", None)
    products = [{"title": "Test Product"}]
    result = service.create_sku(products)
    assert all(p["sku"] == "stub-sku" for p in result)


def test_publish_listing_returns_stub_url_when_no_api_key(monkeypatch):
    monkeypatch.setattr(service, "ETSY_API_KEY", None)
    product = {"title": "Test Product"}
    result = service.publish_listing(product)
    assert result["etsy_url"] == "http://etsy.example/listing"
    assert result["listing_url"] == "http://etsy.example/listing"
