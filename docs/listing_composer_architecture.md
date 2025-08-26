# Listing Composer Architecture

```mermaid
flowchart LR
    UI[Listing Composer UI] -->|save draft| LCAPI[/Listing Composer API/]
    UI -->|load draft| LCAPI
    UI -->|suggest tags| Ideation[Ideation Service]
    Ideation --> Data[(Sales & Search Data)]
    LCAPI --> DB[(Database)]
```
