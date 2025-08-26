import {
  fetchTagSuggestions,
  saveDraft,
  loadDraft,
} from '../services/listings';
import axios from 'axios';

jest.mock('axios');
const mocked = axios as jest.Mocked<typeof axios>;

describe('listing services', () => {
  it('fetches tags from API', async () => {
    mocked.post.mockResolvedValue({ data: ['tag1', 'tag2'] });
    const tags = await fetchTagSuggestions('t', 'd');
    expect(tags).toEqual(['tag1', 'tag2']);
    expect(mocked.post).toHaveBeenCalled();
  });

  it('saves draft via API', async () => {
    mocked.post.mockResolvedValue({ data: { id: 2 } });
    const id = await saveDraft({
      title: '',
      description: '',
      tags: [],
      language: 'en',
      field_order: [],
    });
    expect(id).toBe(2);
    expect(mocked.post).toHaveBeenCalled();
  });

  it('loads draft via API', async () => {
    mocked.get.mockResolvedValue({
      data: { id: 1, title: '', description: '', tags: [], language: 'en', field_order: [] },
    });
    const d = await loadDraft(1);
    expect(d.id).toBe(1);
    expect(mocked.get).toHaveBeenCalled();
  });
});
