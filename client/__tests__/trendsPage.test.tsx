import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import axios from 'axios';

import TrendsPage from '../pages/trends';

jest.mock('axios');

const push = jest.fn();

jest.mock('next/router', () => ({
  useRouter: () => ({ push, query: {} }),
}));

const mockedAxios = axios as jest.Mocked<typeof axios>;

function trendPayload() {
  return {
    cards: [],
    momentum: [{ date: '2026-04-01', etsy_search_volume: 10, google_trends: 8, internal_trend_score: 5 }],
    product_categories: [{ category: 'T-Shirts', listings: 12, demand: 80 }],
    keywords: [
      {
        rank: 1,
        keyword: 'dog mom',
        search_volume: 156000,
        growth: 64.2,
        competition: 34,
        suggested_products: ['T-Shirt', 'Mug'],
        opportunity: 'High',
      },
    ],
    design_ideas: [{ title: 'Dog Mom Floral Typo', opportunity: 'High', product_type: 'T-Shirt' }],
    tag_clusters: [{ cluster: 'dog mom', tags: ['dog mom', 'paw mom'], volume: 156000 }],
    provenance: { source: 'trend_insights', is_estimated: true, updated_at: '', confidence: 0.7 },
  };
}

describe('trend insights page', () => {
  beforeEach(() => {
    mockedAxios.get.mockReset();
    mockedAxios.post.mockReset();
    push.mockReset();
    mockedAxios.get.mockResolvedValue({ data: trendPayload() });
    mockedAxios.post.mockResolvedValue({ data: { id: 1 } });
  });

  it('reloads data when filters change', async () => {
    render(<TrendsPage />);

    await screen.findByRole('button', { name: 'dog mom' });
    fireEvent.change(screen.getByLabelText('Date Range'), { target: { value: '90' } });

    await waitFor(() =>
      expect(mockedAxios.get).toHaveBeenLastCalledWith(
        'http://localhost:8000/api/trends/insights',
        expect.objectContaining({
          params: expect.objectContaining({ lookback_days: 90 }),
        })
      )
    );
  });

  it('saves, watches, and sends a keyword to composer', async () => {
    render(<TrendsPage />);

    await screen.findByRole('button', { name: 'dog mom' });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() =>
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/niches/saved',
        { niche: 'dog mom', score: 156000 },
        expect.any(Object)
      )
    );

    fireEvent.click(screen.getByRole('button', { name: 'Watch' }));
    await waitFor(() =>
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/search/watchlist',
        expect.objectContaining({ item_type: 'trend_keyword', name: 'dog mom' }),
        expect.any(Object)
      )
    );

    expect(screen.getByRole('link', { name: 'Compose' })).toHaveAttribute(
      'href',
      expect.stringContaining('/listing-composer?source=trends&keyword=dog+mom')
    );
  });

  it('adds tag clusters and hands design ideas to composer', async () => {
    render(<TrendsPage />);

    await screen.findByText('Dog Mom Floral Typo');
    fireEvent.click(screen.getByRole('button', { name: 'Add cluster' }));

    await waitFor(() =>
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/search/watchlist',
        expect.objectContaining({ item_type: 'tag_cluster', name: 'dog mom' }),
        expect.any(Object)
      )
    );

    expect(screen.getAllByRole('link', { name: 'Use in Composer' })[1]).toHaveAttribute(
      'href',
      expect.stringContaining('source=trend-design-idea')
    );
  });
});
