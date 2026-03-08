import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import React from 'react';
import SettingsPage from '../pages/settings';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) =>
      ({
        'settings.pageTitle': 'Localized Settings Title',
        'settings.usageQuota': 'Localized Usage Heading',
      }[key] ?? key),
  }),
}));

jest.mock('../components/OAuthConnect', () => () => <div data-testid="oauth-connect">OAuth Connect</div>);
jest.mock('../components/SocialSettings', () => () => <div data-testid="social-settings">Social Settings</div>);
jest.mock('../components/UserQuota', () => () => <div data-testid="user-quota">User Quota</div>);

describe('settings page', () => {
  it('renders translated headings without fallback defaults', () => {
    render(<SettingsPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'Localized Settings Title' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Localized Usage Heading' })).toBeInTheDocument();
    expect(screen.getByTestId('oauth-connect')).toBeInTheDocument();
    expect(screen.getByTestId('social-settings')).toBeInTheDocument();
    expect(screen.getByTestId('user-quota')).toBeInTheDocument();
  });
});
