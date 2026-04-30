import axios from 'axios';

import { fetchLiveTrendStatus, fetchLiveTrends, refreshLiveTrends } from '../services/trends';

jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('trends service', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('fetches live trends with bounded defaults', async () => {
    mockedAxios.get.mockResolvedValueOnce({
      data: { animals: [{ source: 'tiktok', keyword: 'funny cat', category: 'animals', engagement_score: 10, timestamp: '2026-03-06T00:00:00' }] },
    });

    const data = await fetchLiveTrends();

    expect(data.animals[0].keyword).toBe('funny cat');
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/trends/live', {
      params: {
        category: undefined,
        source: undefined,
        lookback_hours: 72,
        limit: 8,
        page: undefined,
        page_size: undefined,
        sort_by: undefined,
        sort_order: undefined,
        include_meta: undefined,
      },
    });
  });

  it('fetches live trends with pagination metadata', async () => {
    mockedAxios.get.mockResolvedValueOnce({
      data: {
        items_by_category: {
          sports: [
            {
              source: 'google_trends_rss',
              keyword: 'cole caufield',
              category: 'sports',
              engagement_score: 100,
              timestamp: '2026-04-27T00:00:00',
            },
          ],
        },
        pagination: { page: 1, page_size: 10, per_group_limit: 10, total: 1, total_by_category: { sports: 1 }, sort_by: 'timestamp', sort_order: 'desc' },
        provenance: { source: 'trendsignal_table', is_estimated: false, updated_at: '2026-04-27T00:00:00', confidence: 0.86 },
      },
    });

    const data = await fetchLiveTrends({
      includeMeta: true,
      page: 1,
      pageSize: 10,
      limit: 10,
      sortBy: 'timestamp',
      sortOrder: 'desc',
    });

    expect(data.pagination.total).toBe(1);
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/trends/live', {
      params: {
        category: undefined,
        source: undefined,
        lookback_hours: 72,
        limit: 10,
        page: 1,
        page_size: 10,
        sort_by: 'timestamp',
        sort_order: 'desc',
        include_meta: true,
      },
    });
  });

  it('posts refresh request', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: { status: 'ok' } });

    await refreshLiveTrends();

    expect(mockedAxios.post).toHaveBeenCalledWith('http://localhost:8000/api/trends/refresh');
  });

  it('fetches refresh status', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: { last_mode: 'live' } });

    const data = await fetchLiveTrendStatus();

    expect(data.last_mode).toBe('live');
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/api/trends/live/status');
  });
});
