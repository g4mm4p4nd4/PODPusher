import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import OAuthCallbackPage from '../pages/oauth/callback/[provider]';
import { completeOAuthCallback } from '../services/oauth';

const translationTable: Record<string, string> = {
  'oauth.preparing': 'Preparing connection...',
  'oauth.connecting': 'Connecting...',
  'oauth.success': 'Linked {{provider}} successfully.',
  'oauth.redirect': 'Redirecting you to settings...',
  'oauth.error': 'OAuth callback failed.',
  'oauth.missingParams': 'Missing OAuth parameters.',
  'oauth.return': 'Return to settings',
  'settings.providers.unknown': 'Connected account',
};

const replaceMock = jest.fn();
const pushMock = jest.fn();
const routerMock = {
  query: {
    provider: 'custom-provider',
    code: 'abc',
    state: 'xyz',
  },
  asPath: '/oauth/callback/custom-provider?code=abc&state=xyz',
  isReady: true,
  replace: replaceMock,
  push: pushMock,
};
const tMock = (key: string, options?: Record<string, unknown>) => {
  const template = translationTable[key] ?? key;
  if (!options) {
    return template;
  }
  return template.replace(/\{\{(\w+)\}\}/g, (_match, token: string) => {
    const value = options[token];
    return value == null ? '' : String(value);
  });
};

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: tMock,
  }),
}));

jest.mock('next/router', () => ({
  useRouter: () => routerMock,
}));

jest.mock('../services/oauth', () => ({
  completeOAuthCallback: jest.fn(),
}));

const mockedCompleteOAuthCallback = completeOAuthCallback as jest.MockedFunction<typeof completeOAuthCallback>;

beforeEach(() => {
  jest.useFakeTimers();
  replaceMock.mockReset();
  pushMock.mockReset();
  mockedCompleteOAuthCallback.mockReset();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

test('uses translated unknown provider label when callback provider is unmapped', async () => {
  mockedCompleteOAuthCallback.mockResolvedValue({ provider: 'custom-provider' });

  render(<OAuthCallbackPage />);

  await waitFor(() => {
    expect(screen.getByText('Linked Connected account successfully.')).toBeInTheDocument();
  });

  expect(mockedCompleteOAuthCallback).toHaveBeenCalledWith(
    'custom-provider',
    'abc',
    'xyz',
    'http://localhost/oauth/callback/custom-provider',
  );
});
