import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import { OAuthConnectCard } from '../components/OAuthConnect';
import type { ProviderStatus } from '../contexts/ProviderContext';
import { useProviders } from '../contexts/ProviderContext';
import { authorizeOAuthProvider, deleteOAuthCredential } from '../services/oauth';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

jest.mock('../contexts/ProviderContext', () => ({
  useProviders: jest.fn(),
}));

jest.mock('../services/oauth', () => ({
  authorizeOAuthProvider: jest.fn(),
  deleteOAuthCredential: jest.fn(),
}));

const mockedUseProviders = useProviders as jest.MockedFunction<typeof useProviders>;
const mockedAuthorizeOAuthProvider = authorizeOAuthProvider as jest.MockedFunction<typeof authorizeOAuthProvider>;
const mockedDeleteOAuthCredential = deleteOAuthCredential as jest.MockedFunction<typeof deleteOAuthCredential>;

const disconnectedStatus: ProviderStatus = {
  provider: 'etsy',
  connected: false,
  accountName: null,
  expiresAt: null,
  isExpiringSoon: false,
  isExpired: false,
};

const connectedStatus: ProviderStatus = {
  provider: 'etsy',
  connected: true,
  accountName: 'shop',
  expiresAt: null,
  isExpiringSoon: false,
  isExpired: false,
};

beforeEach(() => {
  mockedAuthorizeOAuthProvider.mockReset();
  mockedDeleteOAuthCredential.mockReset();
});

test('uses translated fallback when connect fails with non-Error value', async () => {
  mockedUseProviders.mockReturnValue({
    providers: [],
    credentials: new Map(),
    loading: false,
    error: null,
    refresh: jest.fn(async () => {}),
    isConnected: jest.fn(() => false),
    getProviderStatus: jest.fn(() => disconnectedStatus),
    allRequiredConnected: jest.fn(() => false),
  });
  mockedAuthorizeOAuthProvider.mockRejectedValueOnce('boom');

  render(<OAuthConnectCard provider="etsy" description="desc" />);
  fireEvent.click(screen.getByRole('button', { name: 'oauth.connect' }));

  await waitFor(() => expect(screen.getByText('oauth.connectStartError')).toBeInTheDocument());
});

test('uses translated fallback when disconnect fails with non-Error value', async () => {
  mockedUseProviders.mockReturnValue({
    providers: [],
    credentials: new Map(),
    loading: false,
    error: null,
    refresh: jest.fn(async () => {}),
    isConnected: jest.fn(() => true),
    getProviderStatus: jest.fn(() => connectedStatus),
    allRequiredConnected: jest.fn(() => false),
  });
  mockedDeleteOAuthCredential.mockRejectedValueOnce('boom');

  render(<OAuthConnectCard provider="etsy" description="desc" />);
  fireEvent.click(screen.getByRole('button', { name: 'oauth.disconnect' }));
  fireEvent.click(screen.getByRole('button', { name: 'oauth.yes' }));

  await waitFor(() => expect(screen.getByText('oauth.disconnectError')).toBeInTheDocument());
});
