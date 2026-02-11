import React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import UserQuota from '../components/UserQuota';
import {
  createBillingPortalSession,
  fetchCurrentUser,
  imageGeneratedEvent,
} from '../services/user';

jest.mock('../services/user', () => ({
  fetchCurrentUser: jest.fn(),
  createBillingPortalSession: jest.fn(),
  imageGeneratedEvent: 'image:generated',
  quotaRefreshEvent: 'quota:refresh',
}));

const mockedFetch = fetchCurrentUser as jest.Mock;
const mockedCreatePortalSession = createBillingPortalSession as jest.Mock;

afterEach(() => {
  mockedFetch.mockReset();
  mockedCreatePortalSession.mockReset();
});

test('renders a progress bar for metered plans', async () => {
  mockedFetch.mockResolvedValue({ plan: 'free', quota_used: 5, quota_limit: 20 });

  render(<UserQuota />);

  await waitFor(() => expect(screen.getByText('free')).toBeInTheDocument());
  expect(screen.getByText('5/20')).toBeInTheDocument();
  expect(screen.getByText('settings.creditsLeft')).toBeInTheDocument();
  expect(screen.getByTestId('quota-bar')).toHaveStyle({ width: '25%' });
});

test('shows unlimited status for pro plans', async () => {
  mockedFetch.mockResolvedValue({ plan: 'pro', quota_used: 120, quota_limit: null });

  render(<UserQuota />);

  await waitFor(() =>
    expect(screen.getByTestId('quota')).toHaveTextContent('Pro · Unlimited')
  );
});

test('refreshes usage when quota events are emitted', async () => {
  mockedFetch
    .mockResolvedValueOnce({ plan: 'free', quota_used: 2, quota_limit: 20 })
    .mockResolvedValueOnce({ plan: 'free', quota_used: 10, quota_limit: 20 });

  render(<UserQuota />);

  await waitFor(() => expect(screen.getByText('2/20')).toBeInTheDocument());

  await act(async () => {
    window.dispatchEvent(new Event(imageGeneratedEvent));
    await Promise.resolve();
  });

  await waitFor(() => expect(screen.getByText('10/20')).toBeInTheDocument());
});


test('opens billing portal from upgrade CTA using authenticated portal creation', async () => {
  mockedFetch.mockResolvedValue({ plan: 'free', quota_used: 5, quota_limit: 20 });
  mockedCreatePortalSession.mockResolvedValue('https://billing.example.com/portal/session');
  render(<UserQuota />);

  await waitFor(() => expect(screen.getByTestId('upgrade-cta')).toBeInTheDocument());

  await act(async () => {
    screen.getByTestId('upgrade-cta').click();
  });

  expect(mockedCreatePortalSession).toHaveBeenCalledWith('/');
});
