import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import SocialMediaGenerator from '../components/SocialMediaGenerator';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key.split('.').pop() })
}));

jest.mock('../services/socialGenerator', () => ({
  generateSocialPost: jest.fn(() => Promise.resolve({
    caption: 'mock caption',
    image: 'ZmFrZQ=='
  }))
}));

test('generates caption and shows image', async () => {
  render(<SocialMediaGenerator />);
  fireEvent.change(screen.getByPlaceholderText('titleField'), { target: { value: 'Shirt' } });
  fireEvent.change(screen.getByPlaceholderText('typeField'), { target: { value: 'tshirt' } });
  fireEvent.click(screen.getByText('button'));
  expect(await screen.findByDisplayValue('mock caption')).toBeInTheDocument();
  const img = screen.getByRole('img') as HTMLImageElement;
  expect(img.getAttribute('src')).toContain('base64');
});
