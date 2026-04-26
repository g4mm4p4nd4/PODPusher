import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import SocialSettings from '../components/SocialSettings';
import { getPreferences, savePreferences } from '../services/userPreferences';
import { listOAuthCredentials, listOAuthProviders } from '../services/oauth';

const translationTable: Record<string, string> = {
  'settings.title': 'Social Settings',
  'settings.auto': 'Auto social',
  'settings.instagram': 'Instagram handle',
  'settings.facebook': 'Facebook handle',
  'settings.twitter': 'Twitter handle',
  'settings.tiktok': 'TikTok handle',
  'settings.notificationChannels': 'Notification channels',
  'settings.emailNotifications': 'Email notifications',
  'settings.pushNotifications': 'Push notifications',
  'settings.preferences': 'Preferences',
  'settings.defaultLanguage': 'Default language',
  'settings.languages.en': 'Lang English',
  'settings.languages.es': 'Lang Spanish',
  'settings.languages.fr': 'Lang French',
  'settings.languages.de': 'Lang German',
  'settings.currency': 'Currency',
  'settings.currencies.USD': 'Currency USD',
  'settings.currencies.EUR': 'Currency EUR',
  'settings.currencies.GBP': 'Currency GBP',
  'settings.currencies.CAD': 'Currency CAD',
  'settings.currencies.AUD': 'Currency AUD',
  'settings.timezone': 'Timezone',
  'settings.timezones.utc': 'TZ UTC',
  'settings.timezones.americaNewYork': 'TZ New York',
  'settings.timezones.americaChicago': 'TZ Chicago',
  'settings.timezones.americaDenver': 'TZ Denver',
  'settings.timezones.americaLosAngeles': 'TZ Los Angeles',
  'settings.timezones.europeLondon': 'TZ London',
  'settings.timezones.europeParis': 'TZ Paris',
  'settings.timezones.asiaTokyo': 'TZ Tokyo',
  'settings.timezones.australiaSydney': 'TZ Sydney',
  'settings.oauthConnectionsAria': 'OAuth Connections Region',
  'settings.oauthTitle': 'Integrations',
  'settings.save': 'Save',
  'settings.invalidHandle': 'Invalid handle format',
  'settings.providers.etsy': 'Etsy',
  'settings.providers.unknown': 'Connected account',
  'settings.status.disconnected': 'Not connected',
  'settings.connect': 'Connect',
};

const mockTranslate = (key: string) => translationTable[key] ?? key;
const mockReplace = jest.fn();
const mockRouter = {
  query: {} as Record<string, string | string[] | undefined>,
  pathname: '/settings',
  isReady: true,
  replace: mockReplace,
};

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: mockTranslate,
  }),
}));

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

jest.mock('../services/userPreferences', () => ({
  getPreferences: jest.fn(),
  savePreferences: jest.fn(),
}));

jest.mock('../services/oauth', () => ({
  authorizeOAuthProvider: jest.fn(),
  deleteOAuthCredential: jest.fn(),
  listOAuthCredentials: jest.fn(),
  listOAuthProviders: jest.fn(),
}));

const mockedGetPreferences = getPreferences as jest.MockedFunction<typeof getPreferences>;
const mockedSavePreferences = savePreferences as jest.MockedFunction<typeof savePreferences>;
const mockedListOAuthProviders = listOAuthProviders as jest.MockedFunction<typeof listOAuthProviders>;
const mockedListOAuthCredentials = listOAuthCredentials as jest.MockedFunction<typeof listOAuthCredentials>;

beforeEach(() => {
  mockReplace.mockReset();
  mockRouter.query = {};
  mockedGetPreferences.mockReset();
  mockedSavePreferences.mockReset();
  mockedListOAuthProviders.mockReset();
  mockedListOAuthCredentials.mockReset();
  mockedGetPreferences.mockResolvedValue({
    auto_social: true,
    social_handles: {},
    email_notifications: true,
    push_notifications: false,
    preferred_language: 'en',
    preferred_currency: 'USD',
    timezone: 'UTC',
  });
  mockedListOAuthProviders.mockResolvedValue([
    {
      provider: 'etsy',
      auth_url: '',
      token_url: '',
      scope: [],
      use_pkce: true,
    },
  ]);
  mockedListOAuthCredentials.mockResolvedValue([]);
});

async function renderLoadedSocialSettings() {
  render(<SocialSettings />);

  await waitFor(() => {
    expect(mockedGetPreferences).toHaveBeenCalled();
    expect(mockedListOAuthProviders).toHaveBeenCalled();
    expect(mockedListOAuthCredentials).toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Connect' })).not.toBeDisabled();
  });
}

test('renders translated settings option labels and translated oauth region aria-label', async () => {
  await renderLoadedSocialSettings();

  expect(screen.getByRole('option', { name: 'Lang English' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Lang Spanish' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Lang French' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Lang German' })).toBeInTheDocument();

  expect(screen.getByRole('option', { name: 'Currency USD' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Currency EUR' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Currency GBP' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Currency CAD' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'Currency AUD' })).toBeInTheDocument();

  expect(screen.getByRole('option', { name: 'TZ UTC' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'TZ New York' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'TZ Chicago' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'TZ Denver' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'TZ Los Angeles' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'TZ London' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'TZ Paris' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'TZ Tokyo' })).toBeInTheDocument();
  expect(screen.getByRole('option', { name: 'TZ Sydney' })).toBeInTheDocument();

  expect(screen.getByRole('region', { name: 'OAuth Connections Region' })).toBeInTheDocument();
});

test('uses translated unknown provider label when provider key is not mapped', async () => {
  mockedListOAuthProviders.mockReset();
  mockedListOAuthProviders.mockResolvedValue([
    {
      provider: 'custom-provider',
      auth_url: '',
      token_url: '',
      scope: [],
      use_pkce: true,
    },
  ]);

  await renderLoadedSocialSettings();

  expect(screen.getByRole('button', { name: 'Connect' })).toBeInTheDocument();
  expect(screen.getByText('Connected account')).toBeInTheDocument();
});

test('shows translated invalid handle message for malformed social handles', async () => {
  await renderLoadedSocialSettings();

  const instagramInput = screen.getByPlaceholderText('Instagram handle');
  fireEvent.change(instagramInput, { target: { value: 'not valid handle!' } });

  await waitFor(() => expect(screen.getByText('Invalid handle format')).toBeInTheDocument());
});
