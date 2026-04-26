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
    expect(screen.getByText('Drill into category')).toHaveAttribute('href', '/search?category=T-Shirts');
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

  it('reloads when the date range changes and opens event detail', async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        metrics: [],
        keyword_growth: [],
        top_rising_niches: [],
        popular_categories: [{ category: 'Mugs', listings: 8, demand: 70 }],
        seasonal_events: [
          {
            name: "Mother's Day",
            event_date: '2026-05-10',
            days_away: 16,
            priority: 'high',
            recommended_keywords: [{ keyword: 'mothers day mug', volume: 1200 }],
          },
        ],
        recent_drafts: [],
        ab_performance: [],
        notifications: [],
      },
    });

    render(<Home />);
    await screen.findByText('Overview Dashboard');

    fireEvent.change(screen.getByLabelText('Date Range'), { target: { value: '30' } });
    await waitFor(() =>
      expect(mockedAxios.get).toHaveBeenLastCalledWith(
        'http://localhost:8000/api/dashboard/overview',
        expect.objectContaining({
          params: expect.objectContaining({
            date_from: expect.any(String),
            date_to: expect.any(String),
          }),
        })
      )
    );

    fireEvent.click(await screen.findByRole('button', { name: /Mother's Day/i }));
    expect(screen.getByText('mothers day mug')).toBeInTheDocument();
    expect(screen.getByText('Open event detail')).toHaveAttribute('href', "/seasonal-events?event=Mother's%20Day");
  });
});
