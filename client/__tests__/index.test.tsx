import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import axios from 'axios';

import Home from '../pages/index';
import { TrendRefreshStatus } from '../services/trends';

jest.mock('axios');

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('home page live trends', () => {
  beforeEach(() => {
    mockedAxios.get.mockReset();
    mockedAxios.post.mockReset();
  });

  it('loads trends and refresh status from live endpoints', async () => {
    mockedAxios.get.mockImplementation(async url => {
      const value = String(url);
      if (value.includes('/api/trends/live/status')) {
        return {
          data: {
            last_started_at: '2026-03-06T12:00:00',
            last_finished_at: '2026-03-06T12:00:02',
            last_mode: 'live',
            sources_succeeded: ['google_trends_rss'],
            sources_failed: {},
            signals_collected: 2,
            signals_persisted: 1,
          },
        };
      }
      if (value.includes('/api/trends/live')) {
        return {
          data: {
            animals: [
              {
                source: 'google_trends_rss',
                keyword: 'funny cat',
                engagement_score: 9,
                timestamp: '2026-03-06T12:00:00',
              },
            ],
          },
        };
      }
      return { data: { month: 'March', events: ['St Patrick'] } };
    });

    render(<Home />);

    await waitFor(() => expect(screen.getByText('funny cat')).toBeInTheDocument());
    expect(screen.getByText(/index.mode/)).toBeInTheDocument();
    expect(screen.getByText('St Patrick')).toBeInTheDocument();
  });

  it('triggers refresh and reloads trends', async () => {
    let status: TrendRefreshStatus = {
      last_started_at: null,
      last_finished_at: null,
      last_mode: 'idle',
      sources_succeeded: [],
      sources_failed: {},
      signals_collected: 0,
      signals_persisted: 0,
    };
    let trends: Record<string, unknown> = {};

    mockedAxios.get.mockImplementation(async url => {
      const value = String(url);
      if (value.includes('/api/trends/live/status')) {
        return { data: status };
      }
      if (value.includes('/api/trends/live')) {
        return { data: trends };
      }
      return { data: { month: 'March', events: [] } };
    });

    mockedAxios.post.mockImplementation(async () => {
      status = {
        last_started_at: '2026-03-06T12:05:00',
        last_finished_at: '2026-03-06T12:05:02',
        last_mode: 'fallback_stub',
        sources_succeeded: ['stub_seed'],
        sources_failed: { google_trends_rss: 'timeout' },
        signals_collected: 4,
        signals_persisted: 4,
      };
      trends = {
        animals: [
          {
            source: 'stub_seed',
            keyword: 'funny dog shirts',
            engagement_score: 88,
            timestamp: '2026-03-06T12:05:00',
          },
        ],
      };
      return { data: status };
    });

    render(<Home />);

    await waitFor(() => expect(screen.getByRole('button', { name: 'index.refresh' })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'index.refresh' }));

    await waitFor(() => expect(mockedAxios.post).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByText('funny dog shirts')).toBeInTheDocument());
  });
});
