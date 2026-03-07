import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import SocialMediaGenerator from '../components/SocialMediaGenerator';
import { generateSocialPost } from '../services/socialGenerator';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key.split('.').pop() }),
}));

jest.mock('../services/socialGenerator', () => ({
  generateSocialPost: jest.fn(() =>
    Promise.resolve({
      caption: 'mock caption',
      image: 'ZmFrZQ==',
    }),
  ),
}));

const mockedGenerateSocialPost = generateSocialPost as jest.MockedFunction<typeof generateSocialPost>;
let consoleErrorSpy: jest.SpyInstance;

beforeEach(() => {
  consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => undefined);
});

afterEach(() => {
  consoleErrorSpy.mockRestore();
});

test('generates caption and shows image', async () => {
  render(<SocialMediaGenerator />);
  fireEvent.change(screen.getByPlaceholderText('titleField'), { target: { value: 'Shirt' } });
  fireEvent.change(screen.getByPlaceholderText('typeField'), { target: { value: 'tshirt' } });
  fireEvent.click(screen.getByText('button'));

  await waitFor(() => expect(screen.queryByText('loading')).not.toBeInTheDocument());
  expect(await screen.findByDisplayValue('mock caption')).toBeInTheDocument();
  const img = screen.getByRole('img') as HTMLImageElement;
  expect(img.getAttribute('src')).toContain('base64');
});

test('shows translated error when generation fails', async () => {
  mockedGenerateSocialPost.mockRejectedValueOnce(new Error('boom'));

  render(<SocialMediaGenerator />);
  fireEvent.click(screen.getByText('button'));

  expect(await screen.findByRole('alert')).toHaveTextContent('error');
});
