import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import React from 'react';

import Generate from '../pages/generate';

const push = jest.fn();

jest.mock('next/router', () => ({
  useRouter: () => ({ locale: 'en', push }),
}));

jest.mock('../contexts/ProviderContext', () => ({
  useProviders: () => ({
    allRequiredConnected: () => true,
    loading: false,
    getProviderStatus: () => ({ connected: true }),
  }),
}));

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'generate.title': 'Generate Product Idea',
        'generate.placeholder': 'Enter trend term',
        'generate.button': 'Generate',
        'generate.generating': 'Generating...',
        'generate.error': 'Generation failed',
        'generate.connectionRequired': 'Connection Required',
        'generate.connectProviders': 'Connect accounts',
        'generate.goToSettings': 'Go to Settings',
        'generate.results.trends': 'Trend Signals',
        'generate.results.ideas': 'Generated Ideas',
        'generate.results.products': 'Suggested Products',
        'generate.results.description': 'Description',
        'generate.results.price': 'Price',
        'generate.results.tags': 'Tags',
        'generate.results.select': 'Select',
        'generate.results.publish': 'Publish',
        'generate.results.publishReady': 'Ready to publish {{title}} at {{price}}.',
        'generate.results.listing': 'Listing Preview',
        'generate.results.viewListing': 'View listing',
        'generate.results.missingIntegrations': 'Connect integrations',
        'generate.results.noData': 'No data',
        'generate.results.none': 'None',
        'generate.results.unknown': 'Unknown',
        'generate.results.untitled': 'Untitled',
        'publish.price': 'Price',
        'publish.tags': 'Tags',
        'publish.publishNow': 'Publish now',
        'publish.schedule': 'Schedule',
      };
      return translations[key] ?? key;
    },
  }),
}));

jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

beforeEach(() => {
  push.mockReset();
  mockedAxios.post.mockReset();
});

test('routes to schedule when publish step schedule is clicked', async () => {
  mockedAxios.post.mockResolvedValueOnce({
    data: {
      trends: [{ term: 'cats' }],
      ideas: [{ id: 1, term: 'cats', description: 'cat shirt' }],
      products: [{ id: 1, title: 'Cat Shirt', image_url: 'img.png', price: 24.99 }],
      listing: null,
      auth: { missing: [] },
    },
  });

  render(<Generate />);

  fireEvent.change(screen.getByPlaceholderText('Enter trend term'), { target: { value: 'cats' } });
  fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

  await screen.findByText('Cat Shirt');
  fireEvent.click(screen.getByRole('button', { name: 'Select' }));
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));

  await waitFor(() => expect(push).toHaveBeenCalledWith('/schedule'));
});
