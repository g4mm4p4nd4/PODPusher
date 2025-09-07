import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import QuotaDisplay from '../components/QuotaDisplay';
import * as userService from '../services/user';

jest.mock('../services/user');

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (_: string, opts: any) => `${opts.remaining}/${opts.limit} credits`,
    i18n: { language: 'en' },
  }),
}));

const mockedFetch = userService.fetchPlan as jest.Mock;

test('shows remaining credits', async () => {
  mockedFetch.mockResolvedValue({ plan: 'free', quota_used: 5, limit: 20 });
  render(<QuotaDisplay />);
  await waitFor(() =>
    expect(screen.getByTestId('quota')).toHaveTextContent('15/20 credits')
  );
});

test('warns when near limit', async () => {
  mockedFetch.mockResolvedValue({ plan: 'free', quota_used: 19, limit: 20 });
  render(<QuotaDisplay />);
  await waitFor(() =>
    expect(screen.getByTestId('quota')).toHaveClass('text-red-500')
  );
});
