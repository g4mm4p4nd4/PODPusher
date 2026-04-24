import {
  checkListingDraftCompliance,
  fetchTagSuggestions,
  generateListingDraft,
  saveDraft,
  loadDraft,
  scoreListingDraft,
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

  it('calls composer generation, score, and compliance APIs', async () => {
    mocked.post.mockResolvedValueOnce({ data: { title: 'Generated' } });
    await expect(generateListingDraft({ niche: 'Dog Mom Gifts' })).resolves.toEqual({
      title: 'Generated',
    });

    mocked.post.mockResolvedValueOnce({ data: { optimization_score: 92 } });
    await expect(scoreListingDraft({ title: 'T', description: 'D', tags: [] })).resolves.toEqual({
      optimization_score: 92,
    });

    mocked.post.mockResolvedValueOnce({ data: { status: 'compliant' } });
    await expect(checkListingDraftCompliance({ title: 'T', description: 'D', tags: [] })).resolves.toEqual({
      status: 'compliant',
    });
  });
});
