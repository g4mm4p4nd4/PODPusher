import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import axios from 'axios';

import Home from '../pages/index';

jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('overview dashboard', () => {
  beforeEach(() => {
    mockedAxios.get.mockReset();
  });

  it('loads aggregate overview metrics', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        metrics: [
          {
            label: 'Trending Keywords',
            value: 2847,
            delta: 18.6,
            sparkline: [1, 2],
            provenance: { source: 'trend_signals', is_estimated: false, updated_at: '', confidence: 0.9 },
          },
        ],
        keyword_growth: [{ date: '2026-04-01', value: 100 }],
        top_rising_niches: [{ niche: 'Dog Mom Gifts', growth: 64, competition_label: 'Low' }],
        popular_categories: [{ category: 'T-Shirts', listings: 10, demand: 90 }],
        seasonal_events: [{ name: "Mother's Day", event_date: '2026-05-10', priority: 'high' }],
        recent_drafts: [{ id: 1, title: 'Dog Mom Tee', language: 'en' }],
        ab_performance: [{ test: 'Dog Mom Tee v2', ctr: 3.2, lift: 0.8 }],
        notifications: [{ id: 1, message: 'Quota warning', type: 'warning' }],
        provenance: { source: 'aggregate', is_estimated: true, updated_at: '', confidence: 0.7 },
      },
    });

    render(<Home />);

    await waitFor(() => expect(screen.getByText('Overview Dashboard')).toBeInTheDocument());
    expect(screen.getByText('Trending Keywords')).toBeInTheDocument();
    expect(screen.getByText('Dog Mom Gifts')).toBeInTheDocument();
    expect(screen.getByText('Dog Mom Tee')).toBeInTheDocument();
  });

  it('refreshes overview metrics', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        metrics: [],
        keyword_growth: [],
        top_rising_niches: [],
        popular_categories: [],
        seasonal_events: [],
        recent_drafts: [],
        ab_performance: [],
        notifications: [],
      },
    });

    render(<Home />);
    await screen.findByRole('button', { name: 'Refresh' });
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));

    await waitFor(() => expect(mockedAxios.get).toHaveBeenCalledTimes(2));
  });
});
