import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import Analytics from '../pages/analytics';
import { fetchTrendingKeywords } from '../services/analytics';

const translationMock = {
  t: (key: string) => key,
  i18n: { language: 'en' },
};

jest.mock('next-i18next', () => ({
  useTranslation: () => translationMock,
}));

jest.mock('next/head', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../services/analytics');

const mockFetchTrendingKeywords = fetchTrendingKeywords as jest.MockedFunction<typeof fetchTrendingKeywords>;

afterEach(() => {
  jest.clearAllMocks();
});

describe('Analytics page', () => {
  it('renders trending keywords sorted by clicks', async () => {
    mockFetchTrendingKeywords.mockResolvedValueOnce([
      { term: 'Mugs', clicks: 25 },
      { term: 'Stickers', clicks: 60 },
      { term: 'Totes', clicks: 40 },
    ]);

    render(<Analytics />);

    await waitFor(() => expect(mockFetchTrendingKeywords).toHaveBeenCalledTimes(1));

    const dataRows = screen.getAllByRole('row').slice(1);
    expect(dataRows).toHaveLength(3);
    expect(dataRows[0]).toHaveTextContent('Stickers');
    expect(dataRows[1]).toHaveTextContent('Totes');
    expect(dataRows[2]).toHaveTextContent('Mugs');
  });

  it('shows an accessible error message when the request fails', async () => {
    mockFetchTrendingKeywords.mockRejectedValueOnce(new Error('Network error'));

    render(<Analytics />);

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByRole('alert')).toHaveTextContent('analytics.error');
  });

  it('shows an accessible error message when no data is returned', async () => {
    mockFetchTrendingKeywords.mockResolvedValueOnce([]);

    render(<Analytics />);

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());
    expect(screen.getByRole('alert')).toHaveTextContent('analytics.empty');
  });
});
