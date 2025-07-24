import { render, screen, fireEvent } from '@testing-library/react';
import ListingComposer from '../components/ListingComposer';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

test('shows character counts', () => {
  render(<ListingComposer />);
  const titleInput = screen.getByRole('textbox', { name: /title/i });
  fireEvent.change(titleInput, { target: { value: 'hello' } });
  expect(screen.getByTestId('title-count')).toHaveTextContent('5/140');

  const descInput = screen.getByRole('textbox', { name: /description/i });
  fireEvent.change(descInput, { target: { value: 'desc' } });
  expect(screen.getByTestId('desc-count')).toHaveTextContent('4/1000');
});

test('fetches and displays tags', async () => {
  mockedAxios.post.mockResolvedValueOnce({ data: ['cat', 'mug'] });
  render(<ListingComposer />);
  const descInput = screen.getByRole('textbox', { name: /description/i });
  fireEvent.change(descInput, { target: { value: 'cute cat mug' } });
  fireEvent.click(screen.getByTestId('suggest-btn'));

  expect(await screen.findByText('cat')).toBeInTheDocument();
  expect(screen.getByText('mug')).toBeInTheDocument();
});
