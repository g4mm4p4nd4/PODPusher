import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import ListingComposer from '../components/ListingComposer';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key.replace('listings.', '') }),
}));

jest.mock('../services/listings', () => ({
  fetchTagSuggestions: jest.fn(() => Promise.resolve(['one', 'two'])),
  saveDraft: jest.fn(() => Promise.resolve(1)),
  loadDraft: jest.fn(() =>
    Promise.resolve({
      id: 1,
      title: '',
      description: '',
      tags: [],
      language: 'en',
      field_order: [],
    })
  ),
}));

const services = require('../services/listings');

const onPublish = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  onPublish.mockClear();
  localStorage.clear();
});

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

test('saves draft', async () => {
  render(<ListingComposer onPublish={onPublish} />);
  fireEvent.click(screen.getByText('save'));
  expect(services.saveDraft).toHaveBeenCalled();
});

test('automatically fetches suggestions when length threshold is reached', async () => {
  jest.useFakeTimers();
  try {
    render(<ListingComposer onPublish={onPublish} />);

    const titleInput = screen.getAllByRole('textbox')[0];
    fireEvent.change(titleInput, { target: { value: 'a'.repeat(12) } });

    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    expect(services.fetchTagSuggestions).toHaveBeenCalledWith(
      'a'.repeat(12),
      ''
    );

    const suggestionButton = await screen.findByRole('button', { name: 'one' });
    expect(suggestionButton).toBeInTheDocument();
  } finally {
    jest.useRealTimers();
  }
});

test('blocks publishing when limits are exceeded', () => {
  render(<ListingComposer onPublish={onPublish} />);

  const titleInput = screen.getAllByRole('textbox')[0];
  fireEvent.change(titleInput, { target: { value: 'a'.repeat(150) } });

  const titleLabel = screen.getByText('title (150/140)');
  expect(titleLabel).toHaveClass('text-red-600');

  const publishButton = screen.getByRole('button', { name: 'publish' });
  expect(publishButton).toBeDisabled();

  fireEvent.click(publishButton);
  expect(onPublish).not.toHaveBeenCalled();
});
