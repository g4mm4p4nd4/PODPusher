import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';

import {
  Button,
  DetailDrawer,
  GlobalDateRangeControl,
  StatePanel,
} from '../components/ControlCenter';

const mockPush = jest.fn();
let mockRouter = {
  pathname: '/trends',
  query: {} as Record<string, string>,
  isReady: true,
  push: mockPush,
};

jest.mock('next/router', () => ({
  useRouter: () => mockRouter,
}));

beforeEach(() => {
  mockPush.mockReset();
  mockRouter = {
    pathname: '/trends',
    query: {},
    isReady: true,
    push: mockPush,
  };
});

test('global date range initializes from query and writes date query state', () => {
  mockRouter = {
    pathname: '/trends',
    query: { date_start: 'last-30', date_end: 'today', category: 'Mugs' },
    isReady: true,
    push: mockPush,
  };

  render(<GlobalDateRangeControl />);

  expect(screen.getByLabelText('Date Range')).toHaveValue('Last 30 Days');

  fireEvent.change(screen.getByLabelText('Date Range'), {
    target: { value: 'May 12 - May 18, 2025' },
  });

  expect(mockPush).toHaveBeenCalledWith(
    { pathname: '/trends', query: { date_start: '2025-05-12', date_end: '2025-05-18', category: 'Mugs' } },
    undefined,
    { shallow: true }
  );
});

test('state panel exposes loading, empty, error, disabled, and success states', () => {
  render(
    <div>
      <StatePanel state="loading" message="Loading rows" />
      <StatePanel state="empty" message="No rows" />
      <StatePanel state="error" message="Could not load rows" />
      <StatePanel state="disabled" message="Connect integration" />
      <StatePanel state="success" message="Saved" />
    </div>
  );

  expect(screen.getByText('Loading rows')).toBeInTheDocument();
  expect(screen.getByText('No rows')).toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent('Could not load rows');
  expect(screen.getByText('Connect integration')).toBeInTheDocument();
  expect(screen.getByText('Saved')).toBeInTheDocument();
});

test('button supports loading, disabled, and success affordances', () => {
  const onClick = jest.fn();

  render(
    <div>
      <Button loading onClick={onClick}>
        Syncing
      </Button>
      <Button disabled onClick={onClick}>
        Disabled
      </Button>
      <Button success>Saved</Button>
    </div>
  );

  expect(screen.getByRole('button', { name: 'Syncing' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Syncing' })).toHaveAttribute('aria-busy', 'true');
  expect(screen.getByRole('button', { name: 'Disabled' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Saved' })).toBeInTheDocument();
});

test('detail drawer renders actions and closes through icon button', () => {
  const onClose = jest.fn();

  render(
    <DetailDrawer
      open
      title="Keyword detail"
      onClose={onClose}
      actions={<Button>Use in Composer</Button>}
    >
      <p>dog mom</p>
    </DetailDrawer>
  );

  expect(screen.getByLabelText('Keyword detail')).toHaveTextContent('dog mom');
  expect(screen.getByRole('button', { name: 'Use in Composer' })).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Close detail panel' }));

  expect(onClose).toHaveBeenCalledTimes(1);
});
