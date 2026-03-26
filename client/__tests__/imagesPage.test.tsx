import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import axios from 'axios';

import Images from '../pages/images';

const translations: Record<string, string> = {
  'images.title': 'Images',
  'images.ideaId': 'Idea ID',
  'images.style': 'Style',
  'images.provider': 'Provider',
  'images.providers.default': 'Default',
  'images.providers.openai': 'OpenAI',
  'images.providers.stub': 'Stub',
  'images.loading': 'Loading images...',
  'images.empty': 'No generated images yet.',
  'images.error': 'Could not update images. Please try again.',
  'images.source': 'Source',
  'images.delete': 'Delete',
  'images.select': 'Select',
  'images.selected': 'Selected',
  'images.regenerate': 'Regenerate',
};

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => translations[key] ?? key,
  }),
}));

jest.mock('../services/apiBase', () => ({
  getApiBase: jest.fn(() => 'http://localhost:8000'),
  getAuthHeaders: jest.fn(() => ({
    Authorization: 'Bearer token',
    'X-User-Id': '1',
  })),
}));

jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

beforeEach(() => {
  mockedAxios.get.mockReset();
  mockedAxios.post.mockReset();
  mockedAxios.delete.mockReset();
});

test('loads and regenerates images with a provider override', async () => {
  mockedAxios.get
    .mockResolvedValueOnce({
      data: [{ id: 1, idea_id: 1, url: 'https://example.com/original.png', provider: 'openai' }],
    })
    .mockResolvedValueOnce({
      data: [{ id: 2, idea_id: 1, url: 'http://example.com/image.png', provider: 'stub' }],
    });
  mockedAxios.post.mockResolvedValueOnce({ data: [] });

  render(<Images />);

  expect(await screen.findByRole('heading', { name: 'Images' })).toBeInTheDocument();
  expect(await screen.findByText('Source: openai')).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText('Style'), { target: { value: 'editorial' } });
  fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'stub' } });
  fireEvent.click(screen.getByRole('button', { name: 'Regenerate' }));

  await waitFor(() =>
    expect(mockedAxios.post).toHaveBeenCalledWith(
      'http://localhost:8000/api/images/generate',
      {
        idea_id: 1,
        style: 'editorial',
        provider_override: 'stub',
      },
      {
        headers: {
          Authorization: 'Bearer token',
          'X-User-Id': '1',
        },
      },
    )
  );

  expect(await screen.findByText('Source: stub')).toBeInTheDocument();
});

test('deletes an image and shows the empty state', async () => {
  mockedAxios.get
    .mockResolvedValueOnce({
      data: [{ id: 7, idea_id: 1, url: 'https://example.com/delete-me.png', provider: 'openai' }],
    })
    .mockResolvedValueOnce({ data: [] });
  mockedAxios.delete.mockResolvedValueOnce({ data: { status: 'deleted' } });

  render(<Images />);

  fireEvent.click(await screen.findByRole('button', { name: 'Delete' }));

  await waitFor(() =>
    expect(mockedAxios.delete).toHaveBeenCalledWith(
      'http://localhost:8000/api/images/7',
      {
        headers: {
          Authorization: 'Bearer token',
          'X-User-Id': '1',
        },
      },
    )
  );

  expect(await screen.findByText('No generated images yet.')).toBeInTheDocument();
});
