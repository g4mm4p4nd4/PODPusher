import axios from 'axios';

import { createBillingPortalSession } from '../services/user';

jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('user service billing portal', () => {
  const originalApiBase = process.env.NEXT_PUBLIC_API_BASE_URL;

  beforeEach(() => {
    mockedAxios.post.mockReset();
    window.localStorage.clear();
    process.env.NEXT_PUBLIC_API_BASE_URL = 'https://api.example.com/';
  });

  afterAll(() => {
    process.env.NEXT_PUBLIC_API_BASE_URL = originalApiBase;
  });

  it('creates a portal session with auth headers and a resolved API URL', async () => {
    window.localStorage.setItem('pod.session.token', 'token-123');
    window.localStorage.setItem('pod.user.id', '42');
    mockedAxios.post.mockResolvedValue({ data: { portal_url: 'https://billing.example.com/session' } });

    const portalUrl = await createBillingPortalSession('/settings?tab=billing#quota');

    expect(portalUrl).toBe('https://billing.example.com/session');
    expect(mockedAxios.post).toHaveBeenCalledWith(
      'https://api.example.com/api/billing/portal',
      null,
      {
        headers: {
          Authorization: 'Bearer token-123',
          'X-User-Id': '42',
        },
        params: {
          return_url: '/settings?tab=billing#quota',
        },
      }
    );
  });
});
