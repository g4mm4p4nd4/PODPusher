import { render, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';

import { MyApp } from '../pages/_app';
import { logEvent } from '../services/analytics';

jest.mock('next-i18next', () => ({
  appWithTranslation: (c: any) => c,
  useTranslation: () => ({ t: (k: string) => k }),
}));

jest.mock('next/router', () => ({
  useRouter: () => ({
    asPath: '/start',
    events: { on: jest.fn(), off: jest.fn() },
  }),
}));

jest.mock('../services/analytics');

const MockComponent = () => <div />;

describe('App analytics', () => {
  it('logs initial page view', async () => {
    render(
      <MyApp Component={MockComponent} pageProps={{}} router={{} as any} />,
    );
    await waitFor(() => {
      expect(logEvent).toHaveBeenCalledWith('page_view', '/start');
    });
  });
});
