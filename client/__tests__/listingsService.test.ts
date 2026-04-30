import {
  checkListingDraftCompliance,
  exportDraft,
  fetchTagSuggestions,
  generateListingDraft,
  fetchDraftHistory,
  listDrafts,
  listPublishQueue,
  queueDraftForPublish,
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

  it('lists composer drafts and draft revisions with pagination params', async () => {
    mocked.get.mockResolvedValueOnce({
      data: {
        items: [],
        total: 0,
        page: 2,
        page_size: 3,
        sort_by: 'updated_at',
        sort_order: 'desc',
        provenance: {
          source: 'listingdraft_table',
          is_estimated: false,
          updated_at: '2026-04-24T00:00:00',
          confidence: 0.96,
        },
      },
    });
    await expect(listDrafts({ page: 2, page_size: 3 })).resolves.toMatchObject({ page: 2 });
    expect(mocked.get).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/listing-composer/drafts?page=2&page_size=3')
    );

    mocked.get.mockResolvedValueOnce({ data: [{ id: 9, draft_id: 2, title: 'Revision' }] });
    await expect(fetchDraftHistory(2)).resolves.toEqual([{ id: 9, draft_id: 2, title: 'Revision' }]);
    expect(mocked.get).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/listing-composer/drafts/2/history')
    );
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

  it('queues draft publish and exports draft payloads', async () => {
    mocked.post.mockResolvedValueOnce({
      data: { queue_item_id: 7, draft_id: 2, status: 'pending', mode: 'demo' },
    });
    await expect(queueDraftForPublish(2)).resolves.toMatchObject({
      queue_item_id: 7,
      draft_id: 2,
      status: 'pending',
    });

    mocked.get.mockResolvedValueOnce({
      data: {
        items: [{ queue_item_id: 7, draft_id: 2, status: 'pending', mode: 'demo' }],
        total: 1,
        page: 1,
        page_size: 4,
        provenance: {
          source: 'automationjob_table',
          is_estimated: false,
          updated_at: '2026-04-24T00:00:00',
          confidence: 0.94,
        },
      },
    });
    await expect(listPublishQueue({ page: 1, page_size: 4, status: 'pending' })).resolves.toMatchObject({
      total: 1,
    });
    expect(mocked.get).toHaveBeenLastCalledWith(
      expect.stringContaining('/api/listing-composer/publish-queue?page=1&page_size=4&status=pending')
    );

    mocked.get.mockResolvedValueOnce({
      data: {
        draft_id: 2,
        title: 'T',
        description: 'D',
        tags: [],
        metadata: {},
        score: {},
        compliance: {},
        provenance: {},
      },
    });
    await expect(exportDraft(2)).resolves.toMatchObject({ draft_id: 2 });
  });
});
