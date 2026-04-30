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
      mode: 'implementation_required',
      integration_status: {},
      message: 'queued',
      created_at: '2026-04-24T00:00:00',
      provenance: {
        source: 'automationjob_table',
        is_estimated: false,
        updated_at: '2026-04-24T00:00:00',
        confidence: 0.94,
      },
    })
  ),
  listDrafts: jest.fn(() =>
    Promise.resolve({
      items: [
        {
          id: 1,
          title: 'Persisted Draft Title',
          description: 'Persisted draft description',
          tags: ['persisted'],
          language: 'en',
          field_order: [],
          updated_at: '2026-04-24T00:00:00',
          revision_count: 2,
          provenance: {
            source: 'listingdraft_table',
            is_estimated: false,
            updated_at: '2026-04-24T00:00:00',
            confidence: 0.96,
          },
        },
      ],
      total: 6,
      page: 1,
      page_size: 3,
      sort_by: 'updated_at',
      sort_order: 'desc',
      provenance: {
        source: 'listingdraft_table',
        is_estimated: false,
        updated_at: '2026-04-24T00:00:00',
        confidence: 0.96,
      },
    })
  ),
  fetchDraftHistory: jest.fn(() =>
    Promise.resolve([
      {
        id: 11,
        draft_id: 1,
        title: 'Revision Draft Title',
        description: 'Revision draft description',
        tags: ['revision'],
        metadata: {},
        created_at: '2026-04-24T00:00:00',
        provenance: {
          source: 'listingdraftrevision_table',
          is_estimated: false,
          updated_at: '2026-04-24T00:00:00',
          confidence: 0.96,
        },
      },
    ])
  ),
  listPublishQueue: jest.fn((params = {}) =>
    Promise.resolve({
      items: [
        {
          queue_item_id: 9,
          draft_id: 1,
          status: (params as { status?: string }).status === 'failed' ? 'failed' : 'pending',
          mode: 'implementation_required',
          integration_status: {
            etsy: { status: 'needs_implementation' },
            printify: { status: 'needs_implementation' },
          },
          message: 'Draft is local only.',
          created_at: '2026-04-24T00:00:00',
          provenance: {
            source: 'automationjob_table',
            is_estimated: false,
            updated_at: '2026-04-24T00:00:00',
            confidence: 0.94,
          },
        },
      ],
      total: 8,
      page: (params as { page?: number }).page || 1,
      page_size: 4,
      provenance: {
        source: 'automationjob_table',
        is_estimated: false,
        updated_at: '2026-04-24T00:00:00',
        confidence: 0.94,
      },
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

async function renderComposer() {
  render(<ListingComposer onPublish={onPublish} />);
  await screen.findByText('Persisted Draft Title');
}

test('shows character counts and adds tags', async () => {
  await renderComposer();
  const titleInput = screen.getByLabelText(/Title/);
  fireEvent.change(titleInput, { target: { value: 'Hello' } });
  expect(screen.getByText(/5\/140/)).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Suggest Tags' }));
  const tagButton = await screen.findByRole('button', { name: 'one' });
  fireEvent.click(tagButton);
  expect(screen.getAllByText('one').length).toBeGreaterThan(0);
});

test('saves draft', async () => {
  await renderComposer();
  fireEvent.click(screen.getByRole('button', { name: 'Save Draft' }));
  await waitFor(() => expect(services.saveDraft).toHaveBeenCalled());
});

test('automatically fetches suggestions when length threshold is reached', async () => {
  jest.useFakeTimers();
  try {
    render(<ListingComposer onPublish={onPublish} />);
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    const titleInput = screen.getByLabelText(/Title/);
    fireEvent.change(titleInput, { target: { value: 'a'.repeat(12) } });

    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    expect(services.fetchTagSuggestions).toHaveBeenCalledWith(
      'a'.repeat(12),
      expect.stringContaining('first-paint copy is generated locally')
    );

    const suggestionButton = await screen.findByRole('button', { name: 'one' });
    expect(suggestionButton).toBeInTheDocument();
  } finally {
    jest.useRealTimers();
  }
});

test('blocks publishing when limits are exceeded', async () => {
  await renderComposer();

  const titleInput = screen.getByLabelText(/Title/);
  fireEvent.change(titleInput, { target: { value: 'a'.repeat(150) } });

  const titleLabel = screen.getByText('Title (150/140)');
  expect(titleLabel).toHaveClass('text-red-400');

  const publishButton = screen.getByRole('button', { name: 'Publish Queue' });
  expect(publishButton).toBeDisabled();

  fireEvent.click(publishButton);
  expect(onPublish).not.toHaveBeenCalled();
});

test('renders localized language options', async () => {
  await renderComposer();

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
    evidence_title: 'Retro Dog Mom Bestseller',
    evidence_source: 'amazon',
    evidence_url: 'https://example.com/retro-dog-mom',
    evidence_image_url: 'https://example.com/retro-dog-mom.jpg',
  };

  await renderComposer();

  expect(screen.getByRole('textbox', { name: 'Niche' })).toHaveValue('Dog Lovers');
  expect(screen.getByLabelText('Primary Keyword')).toHaveValue('retro dog mom shirt');
  expect(screen.getByLabelText('Product Type')).toHaveValue('Apparel');
  expect(screen.getByLabelText('Occasion')).toHaveValue('Birthday');
  expect(screen.getByLabelText('Style')).toHaveValue('Retro Summer');
  expect(screen.getByRole('button', { name: 'dog mom' })).toBeInTheDocument();
  expect(screen.getByText('Retro Dog Mom Bestseller')).toBeInTheDocument();
  expect(screen.getByText('amazon')).toBeInTheDocument();
  expect(screen.getByText('Prefilled from search')).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Auto-Fill from Niche' }));
  await waitFor(() =>
    expect(services.generateListingDraft).toHaveBeenCalledWith(
      expect.objectContaining({
        metadata: expect.objectContaining({
          market_evidence: expect.objectContaining({
            title: 'Retro Dog Mom Bestseller',
            source: 'amazon',
          }),
        }),
      })
    )
  );
});

test('loads a source-backed draft from direct draft query params', async () => {
  mockRouter.query = { draft: '42' };
  services.loadDraft.mockResolvedValueOnce({
    id: 42,
    title: 'Direct Draft Title',
    description: 'Direct draft description',
    tags: ['direct'],
    language: 'en',
    field_order: ['title', 'description', 'tags'],
    provenance: {
      source: 'listingdraft_table',
      is_estimated: false,
      updated_at: '2026-04-24T00:00:00',
      confidence: 0.96,
    },
  });

  await renderComposer();

  await waitFor(() => expect(services.loadDraft).toHaveBeenCalledWith(42));
  expect(await screen.findByDisplayValue('Direct Draft Title')).toBeInTheDocument();
  expect(screen.getByText('Loaded draft 42')).toBeInTheDocument();
  expect(localStorage.getItem('draftId')).toBe('42');
});

test('renders persisted draft history and publish queue from API', async () => {
  await renderComposer();

  expect(screen.getByText('Persisted Draft Title')).toBeInTheDocument();
  expect(screen.getByText('Revision Draft Title')).toBeInTheDocument();
  expect(screen.getByText('Draft 1')).toBeInTheDocument();
  expect(screen.getAllByText(/Source: listingdraft/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/Source: automationjob_table/).length).toBeGreaterThan(0);

  fireEvent.click(screen.getByRole('button', { name: 'Load Draft 1' }));
  await waitFor(() => expect(services.loadDraft).toHaveBeenCalledWith(1));

  fireEvent.click(screen.getByRole('button', { name: 'Next Drafts' }));
  await waitFor(() => expect(services.listDrafts).toHaveBeenCalledWith(
    expect.objectContaining({ page: 2, page_size: 3 })
  ));

  fireEvent.click(screen.getByRole('button', { name: 'Next Jobs' }));
  await waitFor(() => expect(services.listPublishQueue).toHaveBeenCalledWith(
    expect.objectContaining({ page: 2, page_size: 4 })
  ));

  fireEvent.change(screen.getByLabelText('Queue Status'), { target: { value: 'failed' } });
  await waitFor(() => expect(services.listPublishQueue).toHaveBeenCalledWith(
    expect.objectContaining({ page: 1, page_size: 4, status: 'failed' })
  ));
  expect(await screen.findByText('failed')).toBeInTheDocument();
});

test('queues publish after saving and shows draft/job status', async () => {
  await renderComposer();

  fireEvent.click(screen.getByRole('button', { name: 'Auto-Fill from Niche' }));
  await screen.findByDisplayValue('Generated Title');

  fireEvent.click(screen.getByRole('button', { name: 'Publish Queue' }));

  expect(await screen.findByText('Queue pending: draft 1, job 9')).toBeInTheDocument();
  expect(services.saveDraft).toHaveBeenCalled();
  expect(services.queueDraftForPublish).toHaveBeenCalledWith(1);
  expect(services.listPublishQueue).toHaveBeenCalledWith(
    expect.objectContaining({ page: 1, page_size: 4, status: 'all' })
  );
  expect(onPublish).toHaveBeenCalledWith(
    expect.objectContaining({ id: 1, title: 'Generated Title' })
  );
});

test('exports after saving and shows draft status', async () => {
  await renderComposer();

  fireEvent.click(screen.getByRole('button', { name: 'Auto-Fill from Niche' }));
  await screen.findByDisplayValue('Generated Title');

  fireEvent.click(screen.getByRole('button', { name: 'Export' }));

  expect(await screen.findByText('Export ready: draft 1')).toBeInTheDocument();
  expect(services.saveDraft).toHaveBeenCalled();
  expect(services.exportDraft).toHaveBeenCalledWith(1, 'json');
});
