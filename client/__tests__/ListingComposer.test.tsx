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
  generateListingDraft: jest.fn(() =>
    Promise.resolve({
      title: 'Generated Title',
      description: 'Generated description with enough words for testing a quality listing.',
      tags: ['one', 'two'],
      score: { optimization_score: 92, seo_score: 94, checks: {} },
      compliance: { status: 'compliant', checks: [] },
    })
  ),
  scoreListingDraft: jest.fn(() =>
    Promise.resolve({ optimization_score: 92, seo_score: 94, checks: {} })
  ),
  checkListingDraftCompliance: jest.fn(() =>
    Promise.resolve({ status: 'compliant', checks: [] })
  ),
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
  const titleInput = screen.getByLabelText(/Title/);
  fireEvent.change(titleInput, { target: { value: 'Hello' } });
  expect(screen.getByText(/5\/140/)).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Suggest Tags' }));
  const tagButton = await screen.findByRole('button', { name: 'one' });
  fireEvent.click(tagButton);
  expect(screen.getAllByText('one').length).toBeGreaterThan(0);
});

test('saves draft', async () => {
  render(<ListingComposer onPublish={onPublish} />);
  fireEvent.click(screen.getByRole('button', { name: 'Save Draft' }));
  expect(services.saveDraft).toHaveBeenCalled();
});

test('automatically fetches suggestions when length threshold is reached', async () => {
  jest.useFakeTimers();
  try {
    render(<ListingComposer onPublish={onPublish} />);

    const titleInput = screen.getByLabelText(/Title/);
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

  const titleInput = screen.getByLabelText(/Title/);
  fireEvent.change(titleInput, { target: { value: 'a'.repeat(150) } });

  const titleLabel = screen.getByText('Title (150/140)');
  expect(titleLabel).toHaveClass('text-red-400');

  const publishButton = screen.getByRole('button', { name: 'Publish Queue' });
  expect(publishButton).toBeDisabled();

  fireEvent.click(publishButton);
  expect(onPublish).not.toHaveBeenCalled();
});

test('renders localized language options', () => {
  render(<ListingComposer onPublish={onPublish} />);

  expect(screen.getByDisplayValue('en')).toBeInTheDocument();
});
