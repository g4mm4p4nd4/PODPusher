import { fireEvent, render, screen } from '@testing-library/react';
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
  'nav.schedule': 'Schedule',
  'nav.images': 'Images',
  'nav.analytics': 'Analytics',
  'nav.socialGenerator': 'Social Generator',
  'nav.abTests': 'A/B Tests',
  'nav.settings': 'Settings',
  'nav.searchPlaceholder': 'Search...',
  'nav.notifications': 'Notifications',
};

const mockPush = jest.fn();
let mockRouter = {
  pathname: '/',
  query: {} as Record<string, string>,
  isReady: true,
  push: mockPush,
};

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
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
  mockPush.mockReset();
  mockRouter = {
    pathname: '/',
    query: {},
    isReady: true,
    push: mockPush,
  };
});

test('renders an Images navigation link', async () => {
  render(
    <Layout>
      <div>Child</div>
    </Layout>
  );

  expect(await screen.findByRole('link', { name: 'Images' })).toHaveAttribute('href', '/images');
});

test('renders a Schedule navigation link', async () => {
  render(
    <Layout>
      <div>Child</div>
    </Layout>
  );

  expect(await screen.findByRole('link', { name: 'Schedule' })).toHaveAttribute('href', '/schedule');
});

test('renders primary navigation with icons instead of abbreviation marks', () => {
  render(
    <Layout>
      <div>Child</div>
    </Layout>
  );

  expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('href', '/');
  expect(screen.getByRole('link', { name: 'Trends' })).toHaveAttribute('href', '/trends');
  expect(screen.queryByText('OV')).not.toBeInTheDocument();
  expect(screen.queryByText('TR')).not.toBeInTheDocument();
});

test('global search deep-links to search route with query state', () => {
  render(
    <Layout>
      <div>Child</div>
    </Layout>
  );

  fireEvent.change(screen.getByLabelText('Global search'), { target: { value: 'pickleball mug' } });
  fireEvent.submit(screen.getByLabelText('Global search').closest('form') as HTMLFormElement);

  expect(mockPush).toHaveBeenCalledWith({ pathname: '/search', query: { q: 'pickleball mug' } });
});

test('shell filters update route query state without changing route', () => {
  mockRouter = {
    pathname: '/trends',
    query: { q: 'dog mom' },
    isReady: true,
    push: mockPush,
  };

  render(
    <Layout>
      <div>Child</div>
    </Layout>
  );

  fireEvent.change(screen.getByLabelText('Store'), { target: { value: 'podpusher-etsy' } });

  expect(mockPush).toHaveBeenCalledWith(
    { pathname: '/trends', query: { q: 'dog mom', store: 'podpusher-etsy' } },
    undefined,
    { shallow: true }
  );
});
