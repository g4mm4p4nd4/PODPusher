# Printify Integration

The `packages.integrations.printify` module wraps the Printify REST API.
It performs authenticated requests, applies simple rate limiting and
retries failed calls.  When `PRINTIFY_API_KEY` is missing or
`PRINTIFY_USE_STUB` is truthy, a deterministic stub client is used
instead of the real API.

## Environment variables

| Name | Description |
| ---- | ----------- |
| `PRINTIFY_API_KEY` | Required token for real API calls. |
| `PRINTIFY_SHOP_ID` | Shop identifier used when creating products. |
| `PRINTIFY_USE_STUB` | If set to a truthy value, forces use of the stub client. |

## Example

```python
from packages.integrations import printify

client = printify.get_client()
products = await client.create_skus([{"title": "Tee"}])
```
