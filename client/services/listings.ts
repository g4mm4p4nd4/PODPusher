import axios from 'axios';
import { getApiBase, resolveApiUrl } from './apiBase';

const api = getApiBase();

export async function fetchTagSuggestions(title: string, description: string): Promise<string[]> {
  const res = await axios.post<string[]>(resolveApiUrl('/api/ideation/suggest-tags'), { title, description });
  return res.data;
}

export interface DraftData {
  id?: number;
  title: string;
  description: string;
  tags: string[];
  language: string;
  field_order: string[];
  niche?: string;
  primary_keyword?: string;
  product_type?: string;
  target_audience?: string;
  materials?: string;
  occasion?: string;
  holiday?: string;
  recipient?: string;
  style?: string;
}

export interface PublishQueueResult {
  queue_item_id: number;
  draft_id: number;
  status: string;
  mode: string;
  message: string;
  integration_status: Record<string, unknown>;
  created_at: string;
}

export interface ExportResult {
  draft_id: number;
  title: string;
  description: string;
  tags: string[];
  metadata: Record<string, unknown>;
  score: Record<string, unknown>;
  compliance: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export async function saveDraft(data: DraftData): Promise<number> {
  const res = await axios.post(`${api}/api/listing-composer/drafts`, data);
  return res.data.id;
}

export async function loadDraft(id: number): Promise<DraftData> {
  const res = await axios.get(`${api}/api/listing-composer/drafts/${id}`);
  return res.data as DraftData;
}

export async function queueDraftForPublish(draftId: number): Promise<PublishQueueResult> {
  const res = await axios.post(resolveApiUrl(`/api/listing-composer/drafts/${draftId}/publish-queue`));
  return res.data as PublishQueueResult;
}

export async function exportDraft(draftId: number, format: 'json' | 'csv' = 'json'): Promise<ExportResult | string> {
  const res = await axios.get(resolveApiUrl(`/api/listing-composer/drafts/${draftId}/export?format=${format}`), {
    responseType: format === 'csv' ? 'text' : 'json',
  });
  return res.data as ExportResult | string;
}

export async function generateListingDraft(payload: Record<string, unknown>) {
  const res = await axios.post(resolveApiUrl('/api/listing-composer/generate'), payload);
  return res.data;
}

export async function scoreListingDraft(payload: Record<string, unknown>) {
  const res = await axios.post(resolveApiUrl('/api/listing-composer/score'), payload);
  return res.data;
}

export async function checkListingDraftCompliance(payload: Record<string, unknown>) {
  const res = await axios.post(resolveApiUrl('/api/listing-composer/compliance'), payload);
  return res.data;
}
