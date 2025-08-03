import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import ListingComposer from '../components/ListingComposer';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key.replace('listings.', '') }),
}));

jest.mock('../services/listings', () => ({
  fetchTagSuggestions: jest.fn(() => Promise.resolve(['one', 'two'])),
}));

const onPublish = jest.fn();

test('shows character counts and adds tags', async () => {
  render(<ListingComposer onPublish={onPublish} />);
  const titleInput = screen.getAllByRole('textbox')[0];
  fireEvent.change(titleInput, { target: { value: 'Hello' } });
  expect(screen.getByText(/5\/140/)).toBeInTheDocument();

  fireEvent.click(screen.getByText('suggest'));
  const tagButton = await screen.findByRole('button', { name: 'one' });
  fireEvent.click(tagButton);
  expect(screen.getAllByText('one').length).toBeGreaterThan(0);
});
