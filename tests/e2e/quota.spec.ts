import { test, expect } from '@playwright/test';
import { spawn, ChildProcess } from 'child_process';

const api = 'http://localhost:8000';
let server: ChildProcess;

test.beforeAll(async () => {
  await new Promise((resolve) => {
    const init = spawn('python', [
      '-c',
      'import asyncio; from services.common.database import init_db, get_session; from services.models import Idea;\nasync def run():\n    await init_db();\n    async with get_session() as s:\n        idea = Idea(trend_id=0, description="test");\n        s.add(idea);\n        await s.commit();\n        await s.refresh(idea)\nasyncio.run(run())',
    ]);
    init.on('exit', resolve);
  });
  server = spawn('python', ['-m', 'uvicorn', 'services.image_gen.api:app', '--port', '8000']);
  await new Promise((r) => setTimeout(r, 1000));
});

test.afterAll(() => {
  server.kill();
});

test('requests under quota succeed', async ({ request }) => {
  const uid = '301';
  for (let i = 0; i < 2; i++) {
    const res = await request.post(`${api}/generate`, {
      data: { idea_id: 1, style: 's' },
      headers: { 'X-User-Id': uid },
    });
    expect(res.status()).toBe(200);
  }
});

test('requests beyond quota are blocked', async ({ request }) => {
  const uid = '302';
  for (let i = 0; i < 20; i++) {
    const res = await request.post(`${api}/generate`, {
      data: { idea_id: 1, style: 's' },
      headers: { 'X-User-Id': uid },
    });
    expect(res.status()).toBe(200);
  }
  const res = await request.post(`${api}/generate`, {
    data: { idea_id: 1, style: 's' },
    headers: { 'X-User-Id': uid },
  });
  expect(res.status()).toBe(403);
});
