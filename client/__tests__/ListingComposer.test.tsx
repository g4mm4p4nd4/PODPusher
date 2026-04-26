import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import ListingComposer from '../components/ListingComposer';

const mockRouter = {
  isReady: true,
  query: {},
  push: jest.fn(),
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

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
  queueDraftForPublish: jest.fn(() =>
    Promise.resolve({
      queue_item_id: 9,
      draft_id: 1,
      status: 'pending',
      mode: 'demo',
      integration_status: {},
      message: 'queued',
      created_at: '2026-04-24T00:00:00',
    })
  ),
  exportDraft: jest.fn(() =>
    Promise.resolve({
      draft_id: 1,
      title: 'Generated Title',
      description: 'Generated description',
      tags: [],
      metadata: {},
      score: {},
      compliance: {},
      provenance: {},
    })
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
  mockRouter.query = {};
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
  await waitFor(() => expect(services.saveDraft).toHaveBeenCalled());
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

test('prefills composer from handoff query params', async () => {
  mockRouter.query = {
    source: 'search',
    niche: 'Dog Lovers',
    keyword: 'retro dog mom shirt',
    product_type: 'Apparel',
    tags: 'dog mom,retro beach,summer',
    audience: 'Dog Lovers',
    occasion: 'Birthday',
    style: 'Retro Summer',
  };

  render(<ListingComposer onPublish={onPublish} />);

  expect(screen.getByRole('textbox', { name: 'Niche' })).toHaveValue('Dog Lovers');
  expect(screen.getByLabelText('Primary Keyword')).toHaveValue('retro dog mom shirt');
  expect(screen.getByLabelText('Product Type')).toHaveValue('Apparel');
  expect(screen.getByLabelText('Occasion')).toHaveValue('Birthday');
  expect(screen.getByLabelText('Style')).toHaveValue('Retro Summer');
  expect(screen.getByRole('button', { name: 'dog mom' })).toBeInTheDocument();
  expect(screen.getByText('Prefilled from search')).toBeInTheDocument();
});

test('queues publish after saving and shows draft/job status', async () => {
  render(<ListingComposer onPublish={onPublish} />);

  fireEvent.click(screen.getByRole('button', { name: 'Auto-Fill from Niche' }));
  await screen.findByDisplayValue('Generated Title');

  fireEvent.click(screen.getByRole('button', { name: 'Publish Queue' }));

  expect(await screen.findByText('Queue pending: draft 1, job 9')).toBeInTheDocument();
  expect(services.saveDraft).toHaveBeenCalled();
  expect(services.queueDraftForPublish).toHaveBeenCalledWith(1);
  expect(onPublish).toHaveBeenCalledWith(
    expect.objectContaining({ id: 1, title: 'Generated Title' })
  );
});

test('exports after saving and shows draft status', async () => {
  render(<ListingComposer onPublish={onPublish} />);

  fireEvent.click(screen.getByRole('button', { name: 'Auto-Fill from Niche' }));
  await screen.findByDisplayValue('Generated Title');

  fireEvent.click(screen.getByRole('button', { name: 'Export' }));

  expect(await screen.findByText('Export ready: draft 1')).toBeInTheDocument();
  expect(services.saveDraft).toHaveBeenCalled();
  expect(services.exportDraft).toHaveBeenCalledWith(1, 'json');
});
