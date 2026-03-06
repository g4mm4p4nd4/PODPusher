import { test, expect, type APIRequestContext } from '@playwright/test';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';

const api = 'http://127.0.0.1:18000';
let server: ChildProcess;
const repoRoot = path.resolve(__dirname, '..', '..');

async function waitForHealthcheck(request: APIRequestContext) {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await request.get(`${api}/healthz`);
      if (response.ok()) {
        return;
      }
    } catch (error) {
      // Service is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error('Timed out waiting for image service health check');
}

test.beforeAll(async ({ request }) => {
  await new Promise((resolve) => {
    const init = spawn('python', [
      '-c',
      'import asyncio; from services.common.database import init_db; asyncio.run(init_db())',
    ], { cwd: repoRoot });
    init.on('exit', resolve);
  });
  server = spawn('python', [
    '-m',
    'uvicorn',
    'services.image_gen.api:app',
    '--host',
    '127.0.0.1',
    '--port',
    '18000',
  ], { cwd: repoRoot });
  await waitForHealthcheck(request);
});

test.afterAll(() => {
  server.kill();
});

test('requests under quota succeed', async ({ request }) => {
  const uid = '301';
  for (let i = 0; i < 2; i++) {
    const res = await request.post(`${api}/images`, {
      data: { ideas: ['idea'] },
      headers: { 'X-User-Id': uid },
    });
    expect(res.status()).toBe(200);
  }
});

test('requests beyond quota are blocked', async ({ request }) => {
  const uid = '302';
  for (let i = 0; i < 20; i++) {
    const res = await request.post(`${api}/images`, {
      data: { ideas: ['idea'] },
      headers: { 'X-User-Id': uid },
    });
    expect(res.status()).toBe(200);
  }
  const res = await request.post(`${api}/images`, {
    data: { ideas: ['idea'] },
    headers: { 'X-User-Id': uid },
  });
  expect(res.status()).toBe(403);
});
