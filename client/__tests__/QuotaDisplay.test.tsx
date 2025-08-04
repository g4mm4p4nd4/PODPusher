import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import QuotaDisplay from '../components/QuotaDisplay';
import * as userService from '../services/user';

jest.mock('../services/user');

const mockFetch = userService.fetchPlan as jest.Mock;

beforeEach(() => {
  mockFetch.mockReset();
});

test('shows remaining quota', async () => {
  mockFetch.mockResolvedValue({ plan: 'free', quota_used: 5, limit: 20 });
  render(<QuotaDisplay userId={1} />);
  await waitFor(() =>
    expect(screen.getByTestId('quota')).toHaveTextContent('15 credits left'),
  );
});

test('warns when near limit', async () => {
  mockFetch.mockResolvedValue({ plan: 'free', quota_used: 19, limit: 20 });
  render(<QuotaDisplay userId={1} />);
  await waitFor(() =>
    expect(screen.getByTestId('quota').className).toContain('text-yellow-300'),
  );
});
