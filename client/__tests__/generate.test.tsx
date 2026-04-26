import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import axios from 'axios';
import Generate from '../pages/generate';
import { useProviders } from '../contexts/ProviderContext';

const translationTable: Record<string, string> = {
  'generate.title': 'Generate Product Idea',
  'generate.placeholder': 'Enter trend term',
  'generate.button': 'Generate',
  'generate.generating': 'Generating...',
  'generate.error': 'Localized generation failure',
  'generate.connectionRequired': 'Connection Required',
  'generate.connectProviders': 'Connect required accounts: {{providers}}',
  'generate.goToSettings': 'Go to Settings',
};

const mockTranslate = (key: string, arg?: any) => {
  const template = translationTable[key] ?? key;
  if (arg && typeof arg === 'object' && !Array.isArray(arg)) {
    return Object.entries(arg).reduce(
      (text, [name, value]) => text.replace(`{{${name}}}`, String(value)),
      template
    );
  }
  return template;
};

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: mockTranslate,
    i18n: { language: 'en' },
  }),
}));

jest.mock('next/router', () => ({
  useRouter: () => ({ locale: 'en' }),
}));

jest.mock('../contexts/ProviderContext', () => ({
  useProviders: jest.fn(),
}));

jest.mock('../services/apiBase', () => ({
  getAuthHeaders: jest.fn(() => ({ Authorization: 'Bearer token' })),
  resolveApiUrl: jest.fn((path: string) => `http://localhost:8000${path}`),
}));

jest.mock('axios');

const mockedUseProviders = useProviders as jest.MockedFunction<typeof useProviders>;
const mockedAxios = axios as jest.Mocked<typeof axios>;

beforeEach(() => {
  mockedAxios.post.mockReset();
});

test('shows translated connection warning when required providers are missing', () => {
  mockedUseProviders.mockReturnValue({
    providers: [],
    credentials: new Map(),
    loading: false,
    error: null,
    refresh: jest.fn(async () => {}),
    isConnected: jest.fn(() => false),
    getProviderStatus: jest.fn((provider) => ({
      provider,
      connected: false,
      accountName: null,
      expiresAt: null,
      isExpiringSoon: false,
      isExpired: false,
    })),
    allRequiredConnected: jest.fn(() => false),
  });

  render(<Generate />);

  expect(screen.getByText('Connection Required')).toBeInTheDocument();
  expect(screen.getByText('Connect required accounts: Etsy, Printify')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Go to Settings' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Generate' })).toBeDisabled();
});

test('uses translated fallback error when generation fails with non-Error value', async () => {
  mockedUseProviders.mockReturnValue({
    providers: [],
    credentials: new Map(),
    loading: false,
    error: null,
    refresh: jest.fn(async () => {}),
    isConnected: jest.fn(() => true),
    getProviderStatus: jest.fn((provider) => ({
      provider,
      connected: true,
      accountName: 'connected',
      expiresAt: null,
      isExpiringSoon: false,
      isExpired: false,
    })),
    allRequiredConnected: jest.fn(() => true),
  });
  mockedAxios.post.mockRejectedValueOnce('boom');
  const originalConsoleError = console.error;
  const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation((...args) => {
    if (args.length === 1 && args[0] === 'boom') {
      return;
    }
    originalConsoleError(...args);
  });

  try {
    render(<Generate />);
    fireEvent.change(screen.getByPlaceholderText('Enter trend term'), { target: { value: 'cats' } });
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }));

    await waitFor(() => expect(screen.getByText('Localized generation failure')).toBeInTheDocument());
    expect(consoleErrorSpy).toHaveBeenCalledWith('boom');
  } finally {
    consoleErrorSpy.mockRestore();
  }
});
