import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SearchPage from '../pages/search';

jest.mock('axios', () => ({
  get: jest.fn(() => Promise.resolve({ data: [{ id: 1, image_url: '', rating: 5, tags: ['tag'], idea: 'idea', term: 'term', category: 'cat' }] })),
}));

describe('SearchPage', () => {
  it('updates query state and renders results', async () => {
    render(<SearchPage />);
    const input = screen.getByPlaceholderText('keyword');
    fireEvent.change(input, { target: { value: 'foo' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    expect(await screen.findAllByTestId('result')).toHaveLength(1);
  });
});
