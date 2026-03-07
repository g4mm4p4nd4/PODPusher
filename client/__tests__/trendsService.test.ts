import axios from 'axios';

import { fetchLiveTrends, refreshLiveTrends } from '../services/trends';

jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('trends service', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('fetches live trends with bounded defaults', async () => {
    mockedAxios.get.mockResolvedValueOnce({
      data: { animals: [{ source: 'tiktok', keyword: 'funny cat', engagement_score: 10, timestamp: '2026-03-06T00:00:00' }] },
    });

    const data = await fetchLiveTrends();

    expect(data.animals[0].keyword).toBe('funny cat');
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/trends/live', {
      params: {
        category: undefined,
        source: undefined,
        lookback_hours: 72,
        limit: 8,
      },
    });
  });

  it('posts refresh request', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: { status: 'ok' } });

    await refreshLiveTrends();

    expect(mockedAxios.post).toHaveBeenCalledWith('http://localhost:8000/api/trends/refresh');
  });
});
