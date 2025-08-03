# A/B Testing

The platform lets you experiment with multiple listing variants to find what resonates with buyers.

## Creating a Test
1. Navigate to **A/B Tests** in the dashboard (`/ab-tests`).
2. Enter a descriptive test name.
3. For each variant provide:
   - **Listing ID** – the listing to track.
   - **Variant Title** – the title shown to shoppers.
   - **Variant Description** – the listing description.
4. Add more variants as needed and click **Create**.

Behind the scenes the app stores your variants and begins tracking impressions and clicks.

## Recording Metrics
Use the API to record user interactions:

- `POST /api/ab-tests/{variant_id}/impression`
- `POST /api/ab-tests/{variant_id}/click`

The dashboard updates automatically, showing a table of each variant's impressions, clicks and conversion rate. A bar chart visualises conversion percentages for quick comparison.

## Interpreting Results
Higher conversion rates indicate a more effective variant. Use the chart to see which title and description combination performs best. Once a clear winner emerges, apply that copy to your live listing.
