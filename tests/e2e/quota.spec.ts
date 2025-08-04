import { test, expect } from '@playwright/test';

const api = 'http://localhost:8001';

test('usage within quota succeeds', async ({ request }) => {
  const res = await request.post(`${api}/images`, {
    data: { ideas: ['one'] },
    headers: { 'X-User-Id': '10' },
  });
  expect(res.status()).toBe(200);
});

test('exceeding quota returns 403', async ({ request }) => {
  const userId = '11';
  for (let i = 0; i < 21; i++) {
    const res = await request.post(`${api}/images`, {
      data: { ideas: ['one'] },
      headers: { 'X-User-Id': userId },
    });
    if (i < 20) {
      expect(res.status()).toBe(200);
    } else {
      expect(res.status()).toBe(403);
    }
  }
});
