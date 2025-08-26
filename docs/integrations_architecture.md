# Integrations Architecture

The integration service delegates to dedicated clients for Printify and Etsy. Each client reads its API key from environment variables and falls back to stubbed responses when keys are absent.

```mermaid
flowchart TD
    A[Integration Service] -->|create_sku| B{Printify Client}
    B -->|API key| C[Printify API]
    B -->|missing key| D[Stub SKU]
    A -->|publish_listing| E{Etsy Client}
    E -->|API key| F[Etsy API]
    E -->|missing key| G[Stub Listing]
```
