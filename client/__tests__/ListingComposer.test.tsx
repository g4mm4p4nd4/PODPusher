import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import ListingComposer from '../components/ListingComposer';

jest.mock('axios');
const mocked = axios as jest.Mocked<typeof axios>;

describe('ListingComposer', () => {
  it('shows character counts and suggests tags', async () => {
    mocked.post.mockResolvedValue({ data: ['foo', 'bar'] });
    render(<ListingComposer />);
    const title = screen.getByTestId('title-input');
    fireEvent.change(title, { target: { value: 'Hello' } });
    expect(screen.getByText(/5\/140/)).toBeInTheDocument();
    const desc = screen.getByTestId('description-input');
    fireEvent.change(desc, { target: { value: 'Description here' } });
    expect(screen.getByText(/16\/2000/)).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('suggest-button'));
    await waitFor(() => expect(mocked.post).toHaveBeenCalled());
    expect((screen.getByTestId('tags-input') as HTMLInputElement).value).toBe('foo, bar');
  });
});
