import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';

import SettingsPage from '../pages/settings';
import { fetchSettingsDashboard } from '../services/controlCenter';
import { saveSettingsLocalization } from '../services/operations';

jest.mock('../services/controlCenter', () => ({
  fetchSettingsDashboard: jest.fn(),
}));

jest.mock('../services/operations', () => ({
  configureIntegration: jest.fn(),
  createSettingsBrandProfile: jest.fn(),
  fetchUsageLedger: jest.fn(),
  inviteSettingsUser: jest.fn(),
  saveSettingsLocalization: jest.fn(),
  setDefaultBrandProfile: jest.fn(),
  updateSettingsUserRole: jest.fn(),
}));

const mockedFetchSettings = fetchSettingsDashboard as jest.MockedFunction<typeof fetchSettingsDashboard>;
const mockedSaveLocalization = saveSettingsLocalization as jest.MockedFunction<typeof saveSettingsLocalization>;

const dashboardData = {
  localization: {
    default_language: 'en',
    marketplace_regions: ['US', 'CA'],
    currency: 'USD',
    date_format: 'MMM DD, YYYY',
    localized_niche_targeting: true,
    primary_targeting_region: 'US',
    preview: { language: 'English (US)', currency: '$23.99' },
  },
  regional_niche_preferences: {
    categories: [{ category: 'Apparel', weight: 68 }],
    excluded_global_niches: ['Politics'],
  },
  brand_profiles: [{ id: 1, name: 'PODPusher Default', active: true }],
  integrations: [{ provider: 'etsy', account_name: 'shop', status: 'connected' }],
  quotas: {
    image_generation: { used: 10, limit: 100, percent: 10 },
    ai_credits: { used: 20, limit: 100, percent: 20 },
    active_listings: { used: 1, limit: 10 },
    ab_tests: { used: 2, limit: 100 },
  },
  usage: { image_generation: 10 },
  team_members: [
    {
      id: 1,
      name: 'Admin',
      email: 'admin@podpusher.com',
      role: 'Administrator',
      permissions: ['All permissions'],
      status: 'active',
      last_active_at: new Date().toISOString(),
    },
  ],
};

describe('settings page', () => {
  beforeEach(() => {
    mockedFetchSettings.mockReset();
    mockedSaveLocalization.mockReset();
  });

  it('scopes settings content by selected tab', async () => {
    mockedFetchSettings.mockResolvedValue(dashboardData);

    render(<SettingsPage />);

    expect(await screen.findByText('Settings & Localization')).toBeInTheDocument();
    expect(screen.getByText('Localization Settings')).toBeInTheDocument();
    expect(screen.getByText('admin@podpusher.com')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'General' }));
    expect(screen.queryByText('admin@podpusher.com')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Users & Roles' }));
    expect(screen.getByText('admin@podpusher.com')).toBeInTheDocument();
  });

  it('saves localization changes through the settings API', async () => {
    mockedFetchSettings.mockResolvedValue(dashboardData);
    mockedSaveLocalization.mockResolvedValue({
      saved: true,
      localization: { ...dashboardData.localization, currency: 'GBP' },
    });

    render(<SettingsPage />);

    await screen.findByText('Localization Settings');
    fireEvent.change(screen.getByLabelText('Currency'), { target: { value: 'GBP' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() =>
      expect(mockedSaveLocalization).toHaveBeenCalledWith(
        expect.objectContaining({ currency: 'GBP' })
      )
    );
    expect(await screen.findByRole('status')).toHaveTextContent('Localization settings saved.');
  });

  it('shows brand profiles after tab switching', async () => {
    mockedFetchSettings.mockResolvedValue(dashboardData);

    render(<SettingsPage />);

    fireEvent.click(await screen.findByRole('button', { name: 'Brand Profiles' }));
    expect(screen.getByText('PODPusher Default')).toBeInTheDocument();
  });
});
