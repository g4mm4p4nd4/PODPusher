import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import React from 'react';

import SettingsPage from '../pages/settings';
import { fetchSettingsDashboard } from '../services/controlCenter';

jest.mock('../services/controlCenter', () => ({
  fetchSettingsDashboard: jest.fn(),
}));

const mockedFetchSettings = fetchSettingsDashboard as jest.MockedFunction<typeof fetchSettingsDashboard>;

describe('settings page', () => {
  it('renders localization, quotas, integrations, and users', async () => {
    mockedFetchSettings.mockResolvedValue({
      localization: {
        default_language: 'en',
        marketplace_regions: ['US', 'CA'],
        currency: 'USD',
        date_format: 'MMM DD, YYYY',
        localized_niche_targeting: true,
        preview: { language: 'English (US)', currency: '$23.99' },
      },
      regional_niche_preferences: {
        categories: [{ category: 'Apparel', weight: 68 }],
        excluded_global_niches: ['Politics'],
      },
      brand_profiles: [{ name: 'PODPusher Default', active: true }],
      integrations: [{ provider: 'etsy', account_name: 'shop', status: 'connected' }],
      quotas: {
        image_generation: { used: 10, limit: 100, percent: 10 },
        ai_credits: { used: 20, limit: 100, percent: 20 },
        active_listings: { used: 1, limit: 10 },
        ab_tests: { used: 2, limit: 100 },
      },
      team_members: [
        {
          name: 'Admin',
          email: 'admin@podpusher.com',
          role: 'Administrator',
          permissions: ['All permissions'],
          status: 'active',
          last_active_at: new Date().toISOString(),
        },
      ],
    });

    render(<SettingsPage />);

    expect(await screen.findByText('Settings & Localization')).toBeInTheDocument();
    expect(screen.getByText('Localization Settings')).toBeInTheDocument();
    expect(screen.getByText('PODPusher Default')).toBeInTheDocument();
    expect(screen.getByText('admin@podpusher.com')).toBeInTheDocument();
  });
});
