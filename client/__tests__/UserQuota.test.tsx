import React from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

import UserQuota from '../components/UserQuota';
import {
  createBillingPortalSession,
  fetchCurrentUser,
  imageGeneratedEvent,
} from '../services/user';
import { navigateTo } from '../utils/navigation';

const translationMock = {
  t: (key: string, options?: Record<string, string | number>) => {
    switch (key) {
      case 'quota.plan':
        return String(options?.plan ?? '');
      case 'quota.summary':
        return `${options?.used}/${options?.limit}`;
      case 'quota.remaining':
        return `${options?.count} credits left`;
      case 'quota.unlimited':
        return `${options?.plan} · Unlimited`;
      case 'quota.ariaProgress':
        return `${options?.percentage}% used`;
      default:
        return key;
    }
  },
};

jest.mock('next-i18next', () => ({
  useTranslation: () => translationMock,
}));

jest.mock('../services/user', () => ({
  fetchCurrentUser: jest.fn(),
  createBillingPortalSession: jest.fn(),
  imageGeneratedEvent: 'image:generated',
  quotaRefreshEvent: 'quota:refresh',
}));
jest.mock('../utils/navigation', () => ({
  navigateTo: jest.fn(),
}));

const mockedFetch = fetchCurrentUser as jest.Mock;
const mockedCreatePortalSession = createBillingPortalSession as jest.Mock;
const mockedNavigateTo = navigateTo as jest.Mock;

afterEach(() => {
  mockedFetch.mockReset();
  mockedCreatePortalSession.mockReset();
  mockedNavigateTo.mockReset();
});

test('renders a progress bar for metered plans', async () => {
  mockedFetch.mockResolvedValue({ plan: 'free', quota_used: 5, quota_limit: 20 });

  render(<UserQuota />);

  await waitFor(() => expect(screen.getByText('Free')).toBeInTheDocument());
  expect(screen.getByText('5/20')).toBeInTheDocument();
  expect(screen.getByText('15 credits left')).toBeInTheDocument();
  expect(screen.getByTestId('quota-bar')).toHaveStyle({ width: '25%' });
});

test('shows unlimited status for pro plans', async () => {
  mockedFetch.mockResolvedValue({ plan: 'pro', quota_used: 120, quota_limit: null });

  render(<UserQuota />);

  await waitFor(() => expect(screen.getByText('Pro · Unlimited')).toBeInTheDocument());
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

test('opens billing portal from upgrade CTA using current-location return URL', async () => {
  window.history.replaceState({}, '', '/search?q=abc#results');
  mockedFetch.mockResolvedValue({ plan: 'free', quota_used: 5, quota_limit: 20 });
  mockedCreatePortalSession.mockResolvedValue('https://billing.example.com/portal/session');

  render(<UserQuota />);

  await waitFor(() => expect(screen.getByTestId('upgrade-cta')).toBeInTheDocument());

  await act(async () => {
    screen.getByTestId('upgrade-cta').click();
  });

  expect(mockedCreatePortalSession).toHaveBeenCalledWith('/search?q=abc#results');
  expect(mockedNavigateTo).toHaveBeenCalledWith('https://billing.example.com/portal/session');
});
