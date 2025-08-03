# Etsy Integration

`packages.integrations.etsy` provides a lightweight client for the Etsy
v3 API.  It manages authentication headers, basic rate limiting and
retry logic.  If `ETSY_API_KEY` is absent or `ETSY_USE_STUB` is truthy,
a stub client returns predictable results for testing.

## Environment variables

| Name | Description |
| ---- | ----------- |
| `ETSY_API_KEY` | Required token for real API requests. |
| `ETSY_USE_STUB` | Forces use of the stub client when set to a truthy value. |

## Example

```python
from packages.integrations import etsy

client = etsy.get_client()
url = await client.publish_listing({"title": "Mug"})
```
