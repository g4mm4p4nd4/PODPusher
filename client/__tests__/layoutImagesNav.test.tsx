import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import axios from 'axios';

import Layout from '../components/Layout';

const translations: Record<string, string> = {
  'nav.home': 'Home',
  'nav.generate': 'Generate',
  'nav.categories': 'Categories',
  'nav.designIdeas': 'Design Ideas',
  'nav.suggestions': 'Suggestions',
  'nav.search': 'Search',
  'nav.listings': 'Listings',
  'nav.images': 'Images',
  'nav.analytics': 'Analytics',
  'nav.socialGenerator': 'Social Generator',
  'nav.abTests': 'A/B Tests',
  'nav.settings': 'Settings',
  'nav.searchPlaceholder': 'Search...',
  'nav.notifications': 'Notifications',
};

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));

jest.mock('next/router', () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => translations[key] ?? key,
  }),
}));

jest.mock('../components/LanguageSwitcher', () => () => <div>LanguageSwitcher</div>);
jest.mock('../components/UserQuota', () => () => <div>UserQuota</div>);
jest.mock('../services/apiBase', () => ({
  getApiBase: jest.fn(() => 'http://localhost:8000'),
  getAuthHeaders: jest.fn(() => ({ Authorization: 'Bearer token', 'X-User-Id': '1' })),
}));
jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

beforeEach(() => {
  mockedAxios.get.mockReset();
  mockedAxios.get.mockResolvedValue({ data: [] });
});

test('renders an Images navigation link', async () => {
  render(
    <Layout>
      <div>Child</div>
    </Layout>
  );

  expect(await screen.findByRole('link', { name: 'Images' })).toHaveAttribute('href', '/images');
});
