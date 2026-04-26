import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';

import ABTestingLabPage from '../pages/ab-tests';
import { abAction, createABTest, fetchABDashboard } from '../services/controlCenter';

jest.mock('next/router', () => ({
  useRouter: () => ({ query: {} }),
}));

jest.mock('../services/controlCenter', () => ({
  abAction: jest.fn(),
  createABTest: jest.fn(),
  fetchABDashboard: jest.fn(),
}));

const mockedFetch = fetchABDashboard as jest.MockedFunction<typeof fetchABDashboard>;
const mockedCreate = createABTest as jest.MockedFunction<typeof createABTest>;
const mockedAction = abAction as jest.MockedFunction<typeof abAction>;

const baseExperiment = {
  id: 7,
  name: 'Retro Sunset Tee - Thumbnail Test',
  product_id: 101,
  product: 'Retro Beach Sunset Tee',
  experiment_type: 'thumbnail',
  status: 'running',
  start_time: '2025-05-12T00:00:00',
  end_time: null,
  impressions: 300,
  clicks: 18,
  ctr: 6,
  ctr_lift: 25,
  confidence: 98,
  significant: true,
  winner: { id: 72, name: 'Thumbnail B', weight: 0.5, impressions: 150, clicks: 10, ctr: 6.67 },
  variants: [
    { id: 71, name: 'Thumbnail A', weight: 0.5, impressions: 150, clicks: 8, ctr: 5.33 },
    { id: 72, name: 'Thumbnail B', weight: 0.5, impressions: 150, clicks: 10, ctr: 6.67 },
  ],
  insights: ['Thumbnail B is driving higher CTR with a 25% lift.'],
  integration_status: {
    listing_push: 'local_state',
    message: 'Winner push updates local experiment state.',
  },
  provenance: { source: 'abtest_table', is_estimated: false, updated_at: '', confidence: 0.94 },
};

function dashboard(experiments = [baseExperiment]) {
  return {
    cards: [
      {
        label: 'Active Tests',
        value: experiments.filter((item) => item.status === 'running').length,
        delta: 15,
        sparkline: [1, 2],
        provenance: { source: 'abtest_table', is_estimated: false, updated_at: '', confidence: 0.94 },
      },
    ],
    experiments,
    product_options: [
      { id: 101, name: 'Retro Beach Sunset Tee' },
      { id: 102, name: 'Dog Mom Vintage Hoodie' },
    ],
    provenance: { source: 'ab_dashboard', is_estimated: false, updated_at: '', confidence: 0.94 },
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

test('renders filters, selected detail, and winner confidence', async () => {
  mockedFetch.mockResolvedValue(dashboard());

  render(<ABTestingLabPage />);

  expect(await screen.findByText('A/B Testing Lab')).toBeInTheDocument();
  expect(screen.getByText('Retro Sunset Tee - Thumbnail Test')).toBeInTheDocument();
  expect(screen.getByText('98%')).toBeInTheDocument();
  expect(screen.getAllByText('Thumbnail B').length).toBeGreaterThan(0);

  fireEvent.change(screen.getByPlaceholderText('Search tests, products, variables...'), {
    target: { value: 'sunset' },
  });

  await waitFor(() =>
    expect(mockedFetch).toHaveBeenLastCalledWith(
      expect.objectContaining({ search: 'sunset' })
    )
  );
});

test('creates an A/B test with product, variable, variants, and split', async () => {
  const createdExperiment = {
    ...baseExperiment,
    id: 12,
    name: 'Dog Mom Title Test',
    product_id: 102,
    product: 'Dog Mom Vintage Hoodie',
    experiment_type: 'title',
    variants: [
      { id: 121, name: 'Title A', weight: 0.6, impressions: 0, clicks: 0, ctr: 0 },
      { id: 122, name: 'Title B', weight: 0.4, impressions: 0, clicks: 0, ctr: 0 },
    ],
  };
  mockedFetch
    .mockResolvedValueOnce(dashboard())
    .mockResolvedValueOnce(dashboard([baseExperiment, createdExperiment]));
  mockedCreate.mockResolvedValue({ id: 12 });

  render(<ABTestingLabPage />);

  await screen.findByText('Retro Sunset Tee - Thumbnail Test');
  fireEvent.change(screen.getByPlaceholderText('Retro Sunset Tee - Title Test'), {
    target: { value: 'Dog Mom Title Test' },
  });
  fireEvent.change(screen.getByDisplayValue('Select a product'), {
    target: { value: '102' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Title' }));
  fireEvent.change(screen.getByPlaceholderText('Control'), { target: { value: 'Title A' } });
  fireEvent.change(screen.getByPlaceholderText('Challenger'), { target: { value: 'Title B' } });
  fireEvent.change(screen.getByDisplayValue('50% / 50%'), { target: { value: '60/40' } });
  fireEvent.click(screen.getAllByRole('button', { name: 'Create A/B Test' })[1]);

  await waitFor(() =>
    expect(mockedCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Dog Mom Title Test',
        product_id: 102,
        experiment_type: 'title',
        variants: [
          { name: 'Title A', weight: 0.6 },
          { name: 'Title B', weight: 0.4 },
        ],
      })
    )
  );
  expect(await screen.findByText('Created A/B test in local experiment state.')).toBeInTheDocument();
});

test('action mutation reloads visible selected state', async () => {
  mockedFetch
    .mockResolvedValueOnce(dashboard())
    .mockResolvedValueOnce(dashboard([{ ...baseExperiment, status: 'paused' }]));
  mockedAction.mockResolvedValue({ id: 7, status: 'paused' });

  render(<ABTestingLabPage />);

  await screen.findByText('Retro Sunset Tee - Thumbnail Test');
  fireEvent.click(screen.getByRole('button', { name: 'Pause Test' }));

  await waitFor(() => expect(mockedAction).toHaveBeenCalledWith(7, 'pause'));
  expect(await screen.findByText('Experiment state updated.')).toBeInTheDocument();
  expect(screen.getAllByText('paused').length).toBeGreaterThan(0);
});

test('pushes the winning variant to listing through the visible quick action', async () => {
  mockedFetch.mockResolvedValue(dashboard());
  mockedAction.mockResolvedValue({
    id: 7,
    status: 'pushed',
    demo_state: true,
    integration_status: {
      listing_push: 'local_state',
      message: 'Winner pushed into listing draft state.',
    },
  });

  render(<ABTestingLabPage />);

  await screen.findByText('Retro Sunset Tee - Thumbnail Test');
  const pushWinner = screen.getByRole('button', { name: 'Push Winner to Listing' });
  expect(pushWinner).toBeVisible();

  fireEvent.click(pushWinner);

  await waitFor(() => expect(mockedAction).toHaveBeenCalledWith(7, 'push-winner'));
  expect(await screen.findByRole('status')).toHaveTextContent(
    'Winner pushed into listing draft state.'
  );
  expect(screen.getAllByText('pushed').length).toBeGreaterThan(0);
});
