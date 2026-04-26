import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';

import NicheSuggestionsPage from '../pages/niches';
import { fetchNicheSuggestions, saveBrandProfile, saveNiche } from '../services/controlCenter';

const mockRouter = {
  push: jest.fn(),
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

jest.mock('../services/controlCenter', () => ({
  fetchNicheSuggestions: jest.fn(),
  saveBrandProfile: jest.fn(),
  saveNiche: jest.fn(),
}));

const mockedFetchNiches = fetchNicheSuggestions as jest.MockedFunction<typeof fetchNicheSuggestions>;
const mockedSaveBrandProfile = saveBrandProfile as jest.MockedFunction<typeof saveBrandProfile>;
const mockedSaveNiche = saveNiche as jest.MockedFunction<typeof saveNiche>;

const nichePayload = {
  profile: {
    tone: 'Humorous, Positive',
    audience: 'Adults, Parents',
    interests: ['Pets', 'Coffee', 'Outdoors'],
    banned_topics: ['Politics', 'Religion'],
    preferred_products: ['Apparel', 'Mugs', 'Totes'],
  },
  cards: [],
  niches: [
    {
      niche: 'Outdoor Adventure',
      keyword: 'adventure is calling',
      demand_trend: [10, 20, 30],
      competition: 42,
      profitability: 'High',
      estimated_profit: 4.65,
      audience_overlap: 58,
      brand_fit_score: 87,
      brand_fit_label: 'Great',
      products: ['Apparel', 'Mugs'],
      saved: false,
      why: ['Search trend is rising.', 'Suitable products: Apparel, Mugs.'],
    },
  ],
  suggested_phrases: [],
  design_inspiration: [],
  localized_variants: [],
};

describe('niche suggestions handoffs', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedFetchNiches.mockResolvedValue(nichePayload);
    mockedSaveBrandProfile.mockResolvedValue({});
    mockedSaveNiche.mockResolvedValue({});
  });

  it('saves complete brand profile fields', async () => {
    render(<NicheSuggestionsPage />);

    await screen.findByDisplayValue('Politics, Religion');
    fireEvent.change(screen.getByDisplayValue('Politics, Religion'), {
      target: { value: 'Violence, Trademarks' },
    });
    fireEvent.change(screen.getByDisplayValue('Apparel, Mugs, Totes'), {
      target: { value: 'T-Shirts, Stickers' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Save Profile' }));

    await waitFor(() =>
      expect(mockedSaveBrandProfile).toHaveBeenCalledWith(
        expect.objectContaining({
          banned_topics: ['Violence', 'Trademarks'],
          preferred_products: ['T-Shirts', 'Stickers'],
        })
      )
    );
  });

  it('saves selected niche and exposes composer and A/B handoffs', async () => {
    render(<NicheSuggestionsPage />);

    expect((await screen.findAllByText('Outdoor Adventure')).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: 'Save Niche' }));

    await waitFor(() =>
      expect(mockedSaveNiche).toHaveBeenCalledWith(
        'Outdoor Adventure',
        87,
        expect.objectContaining({ keyword: 'adventure is calling' })
      )
    );

    const createListing = screen.getByRole('link', { name: 'Create Listing' });
    expect(createListing).toHaveAttribute(
      'href',
      expect.stringContaining('/listing-composer?source=niches')
    );
    expect(createListing).toHaveAttribute('href', expect.stringContaining('niche=Outdoor+Adventure'));

    expect(screen.getByRole('link', { name: 'Start A/B Test' })).toHaveAttribute(
      'href',
      expect.stringContaining('/ab-tests?source=niche')
    );
  });
});
