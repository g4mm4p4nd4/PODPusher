import { fetchTagSuggestions } from '../services/listings';
import axios from 'axios';

jest.mock('axios');
const mocked = axios as jest.Mocked<typeof axios>;

describe('fetchTagSuggestions', () => {
  it('fetches tags from API', async () => {
    mocked.post.mockResolvedValue({ data: ['tag1', 'tag2'] });
    const tags = await fetchTagSuggestions('t', 'd');
    expect(tags).toEqual(['tag1', 'tag2']);
    expect(mocked.post).toHaveBeenCalled();
  });
});
