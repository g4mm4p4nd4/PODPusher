import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import React from 'react';

import SearchPage from '../pages/search';
import {
  addToWatchlist,
  fetchSearchInsights,
  generateSearchTags,
  saveSearch,
} from '../services/controlCenter';

const mockRouter = {
  query: {},
  push: jest.fn(),
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

jest.mock('../services/controlCenter', () => ({
  addToWatchlist: jest.fn(),
  fetchSearchInsights: jest.fn(),
  generateSearchTags: jest.fn(),
  saveSearch: jest.fn(),
}));

const mockedFetchSearch = fetchSearchInsights as jest.MockedFunction<typeof fetchSearchInsights>;
const mockedAddToWatchlist = addToWatchlist as jest.MockedFunction<typeof addToWatchlist>;
const mockedGenerateSearchTags = generateSearchTags as jest.MockedFunction<typeof generateSearchTags>;
const mockedSaveSearch = saveSearch as jest.MockedFunction<typeof saveSearch>;

const searchPayload = {
  total: 2,
  results: [
    {
      id: 1,
      name: 'Retro Dog Mom T-Shirt',
      category: 'Apparel',
      rating: 4.6,
      trend_score: 92,
      demand_signal: 'High',
      keyword: 'dog mom summer vibes',
      price: 18.99,
    },
    {
      id: 2,
      name: 'Pickleball Mom Tumbler',
      category: 'Drinkware',
      rating: 4.7,
      trend_score: 88,
      demand_signal: 'High',
      keyword: 'pickleball gifts',
      price: 21.99,
    },
  ],
  phrase_suggestions: ['dog mom summer vibes'],
  design_inspiration: [],
  related_niches: ['Dog Lovers'],
  saved_searches: [
    {
      id: 1,
      name: 'Dog Mom Summer',
      query: 'dog mom',
      filters: { category: 'Apparel', marketplace: 'etsy', season: 'Summer', niche: 'Dog Lovers' },
      result_count: 48,
    },
  ],
  recent_queries: [{ query: 'teacher coffee mug', age: '3h ago' }],
  comparison: [],
};

describe('search suggestions workflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRouter.query = {};
    mockedFetchSearch.mockResolvedValue(searchPayload);
    mockedAddToWatchlist.mockResolvedValue({});
    mockedGenerateSearchTags.mockResolvedValue(['dog mom', 'retro beach', 'summer tee']);
    mockedSaveSearch.mockResolvedValue({});
  });

  it('adds selected search result to watchlist', async () => {
    render(<SearchPage />);

    const row = await screen.findByText('Retro Dog Mom T-Shirt');
    fireEvent.click(within(row.closest('tr') as HTMLElement).getByRole('button', { name: 'Watch' }));

    await waitFor(() =>
      expect(mockedAddToWatchlist).toHaveBeenCalledWith(
        expect.objectContaining({
          item_type: 'product',
          name: 'Retro Dog Mom T-Shirt',
        })
      )
    );
    expect(screen.getByText('Added Retro Dog Mom T-Shirt to watchlist')).toBeInTheDocument();
  });

  it('sends selected result to composer with query handoff params', async () => {
    render(<SearchPage />);

    const row = await screen.findByText('Retro Dog Mom T-Shirt');
    const composeLink = within(row.closest('tr') as HTMLElement).getByRole('link', { name: 'Compose' });
    expect(composeLink).toHaveAttribute('href', expect.stringContaining('/listing-composer?source=search'));
    expect(composeLink).toHaveAttribute('href', expect.stringContaining('keyword=dog+mom+summer+vibes'));
    expect(composeLink).toHaveAttribute('href', expect.stringContaining('product_type=Apparel'));
  });

  it('generates tags for a result and includes them in composer handoff', async () => {
    render(<SearchPage />);

    const row = await screen.findByText('Retro Dog Mom T-Shirt');
    fireEvent.click(within(row.closest('tr') as HTMLElement).getByRole('button', { name: 'Tags' }));

    expect(await screen.findByText('Generated 3 tags')).toBeInTheDocument();
    expect(screen.getByText('retro beach')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('checkbox', { name: 'Select Retro Dog Mom T-Shirt' }));
    expect(screen.getByRole('link', { name: 'Send to Composer' })).toHaveAttribute(
      'href',
      expect.stringContaining('tags=dog+mom%2Cretro+beach%2Csummer+tee')
    );
  });

  it('saves search filters and reuses recent queries', async () => {
    render(<SearchPage />);

    await screen.findByText('Retro Dog Mom T-Shirt');
    fireEvent.click(screen.getByText('teacher coffee mug'));
    fireEvent.click(screen.getByRole('button', { name: 'Save Search' }));

    await waitFor(() =>
      expect(mockedSaveSearch).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'teacher coffee mug',
          filters: expect.objectContaining({
            rating: '4',
            price_band: '$10-$25',
            marketplace: 'etsy',
            season: 'Summer',
          }),
        })
      )
    );
  });
});
