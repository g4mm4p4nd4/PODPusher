import { defineConfig } from '@playwright/test';

export default defineConfig({
  webServer: [
    {
      command:
        "bash -c 'python - <<\"PY\"\nfrom services.common.database import init_db\nimport asyncio\nasyncio.run(init_db())\nPY\nuvicorn services.gateway.api:app --port 8000'",
      port: 8000,
      timeout: 120 * 1000,
      reuseExistingServer: true,
    },
    {
      command: 'uvicorn services.image_gen.api:app --port 8001',
      port: 8001,
      timeout: 120 * 1000,
      reuseExistingServer: true,
    },
    {
      command: 'NEXT_TELEMETRY_DISABLED=1 npm run dev --prefix client',
      port: 3000,
      timeout: 120 * 1000,
      reuseExistingServer: true,
    },
  ],
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
  },
});
