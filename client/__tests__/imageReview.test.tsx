import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import React from 'react';
import ImageReview from '../pages/images/review';

document.body.setAttribute('id', 'root');

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: { defaultValue?: string }) => options?.defaultValue ?? key,
  }),
}));

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

const intersectionObservers: Array<(entries: IntersectionObserverEntry[]) => void> = [];

beforeEach(() => {
  mockedAxios.get.mockReset();
  mockedAxios.put.mockReset();
  mockedAxios.isAxiosError.mockImplementation(
    (error: any): error is any => Boolean(error?.isAxiosError)
  );

  intersectionObservers.length = 0;
  (window as unknown as { IntersectionObserver?: unknown }).IntersectionObserver = class {
    private readonly callback: (entries: IntersectionObserverEntry[]) => void;

    constructor(callback: (entries: IntersectionObserverEntry[]) => void) {
      this.callback = callback;
      intersectionObservers.push(callback);
    }

    observe() {
      // no-op for tests
    }

    disconnect() {
      // no-op for tests
    }

    unobserve() {
      // no-op for tests
    }

    takeRecords(): IntersectionObserverEntry[] {
      return [];
    }
  } as unknown as typeof IntersectionObserver;
});

const renderWithProduct = async (productOverrides: Partial<{ rating: number | null; tags: string[]; flagged: boolean }> = {}) => {
  mockedAxios.get.mockResolvedValue({
    data: {
      items: [
        {
          id: 1,
          name: 'Mock Product',
          image_url: 'https://example.com/image.jpg',
          rating: productOverrides.rating ?? null,
          tags: productOverrides.tags ?? [],
          flagged: productOverrides.flagged ?? false,
        },
      ],
      nextPage: null,
      hasMore: false,
    },
  });

  mockedAxios.put.mockResolvedValue({ data: {} });

  render(<ImageReview />);
  await waitFor(() => expect(mockedAxios.get).toHaveBeenCalled());
  await screen.findByTestId('image-card-1');
};

test('updates rating when a star is clicked', async () => {
  await renderWithProduct({ rating: null });

  const star = await screen.findByTestId('star-1-4');
  fireEvent.click(star);

  await waitFor(() => expect(mockedAxios.put).toHaveBeenCalledWith(expect.any(String), { rating: 4 }));
  expect(star).toHaveAttribute('aria-pressed', 'true');
});

test('adds a new tag through the input field', async () => {
  await renderWithProduct({ tags: ['existing'] });

  const input = screen.getByLabelText('Add tag input');
  fireEvent.change(input, { target: { value: 'new-tag' } });
  fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

  await waitFor(() => expect(mockedAxios.put).toHaveBeenCalledWith(expect.any(String), { tags: ['existing', 'new-tag'] }));
  expect(screen.getByText('new-tag')).toBeInTheDocument();
});

test('toggles the flag checkbox', async () => {
  await renderWithProduct({ flagged: false });

  const flagToggle = screen.getByTestId('flag-toggle-1');
  fireEvent.click(flagToggle);

  await waitFor(() => expect(mockedAxios.put).toHaveBeenCalledWith(expect.any(String), { flagged: true }));
  expect(flagToggle).toBeChecked();
});

test('shows optimistic rating before request completes', async () => {
  mockedAxios.get.mockResolvedValue({
    data: {
      items: [
        {
          id: 1,
          name: 'Mock Product',
          image_url: 'https://example.com/image.jpg',
          rating: 1,
          tags: [],
          flagged: false,
        },
      ],
      nextPage: null,
      hasMore: false,
    },
  });

  let resolvePut: (() => void) | undefined;
  mockedAxios.put.mockImplementation(
    () =>
      new Promise<void>(resolve => {
        resolvePut = resolve;
      })
  );

  render(<ImageReview />);
  await screen.findByTestId('image-card-1');

  const star = screen.getByTestId('star-1-5');
  fireEvent.click(star);

  expect(star).toHaveAttribute('aria-pressed', 'true');

  resolvePut?.();
  await waitFor(() => expect(mockedAxios.put).toHaveBeenCalled());
});

test('rolls back state and shows error message when update fails', async () => {
  mockedAxios.get.mockResolvedValue({
    data: {
      items: [
        {
          id: 1,
          name: 'Mock Product',
          image_url: 'https://example.com/image.jpg',
          rating: 2,
          tags: ['alpha'],
          flagged: false,
        },
      ],
      nextPage: null,
      hasMore: false,
    },
  });

  mockedAxios.put.mockRejectedValue({
    response: { data: { detail: 'Update failed' } },
    isAxiosError: true,
  });

  render(<ImageReview />);
  await screen.findByTestId('image-card-1');

  const star = screen.getByTestId('star-1-5');
  fireEvent.click(star);

  await waitFor(() => expect(mockedAxios.put).toHaveBeenCalled());
  await waitFor(() => expect(screen.getByTestId('star-1-2')).toHaveAttribute('aria-pressed', 'true'));
  expect(screen.getByRole('alert')).toHaveTextContent('Update failed');
});
