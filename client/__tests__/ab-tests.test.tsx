import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import AbTests from '../pages/ab-tests';

jest.mock('axios');
const mocked = axios as jest.Mocked<typeof axios>;

test('creates an A/B test and displays metrics', async () => {
  mocked.post.mockResolvedValueOnce({ data: { id: 1 } });
  mocked.get.mockResolvedValueOnce({ data: { id: 1, variants: [] } });
  render(<AbTests />);
  fireEvent.change(screen.getByLabelText(/Title A/i), { target: { value: 'A' } });
  fireEvent.change(screen.getByLabelText(/Title B/i), { target: { value: 'B' } });
  fireEvent.click(screen.getByText(/Create Test/i));
  await waitFor(() => expect(mocked.post).toHaveBeenCalled());
  await waitFor(() => expect(screen.getByText(/Test ID: 1/)).toBeInTheDocument());
});
