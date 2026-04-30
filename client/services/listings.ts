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
  updated_at?: string;
  revision_count?: number;
  provenance?: Provenance;
}

export interface Provenance {
  source: string;
  is_estimated: boolean;
  updated_at: string;
  confidence: number;
}

export interface DraftRevision {
  id: number;
  draft_id: number;
  title: string;
  description: string;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  provenance: Provenance;
}

export interface DraftListResponse {
  items: DraftData[];
  total: number;
  page: number;
  page_size: number;
  sort_by: string;
  sort_order: string;
  provenance: Provenance;
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

export interface PublishQueueListResponse {
  items: PublishQueueResult[];
  total: number;
  page: number;
  page_size: number;
  provenance: Provenance;
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

export async function listDrafts(params: {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: 'updated_at' | 'title';
  sort_order?: 'asc' | 'desc';
} = {}): Promise<DraftListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : '';
  const res = await axios.get(resolveApiUrl(`/api/listing-composer/drafts${suffix}`));
  return res.data as DraftListResponse;
}

export async function fetchDraftHistory(draftId: number): Promise<DraftRevision[]> {
  const res = await axios.get(resolveApiUrl(`/api/listing-composer/drafts/${draftId}/history`));
  return res.data as DraftRevision[];
}

export async function queueDraftForPublish(draftId: number): Promise<PublishQueueResult> {
  const res = await axios.post(resolveApiUrl(`/api/listing-composer/drafts/${draftId}/publish-queue`));
  return res.data as PublishQueueResult;
}

export async function listPublishQueue(params: {
  page?: number;
  page_size?: number;
  status?: string;
} = {}): Promise<PublishQueueListResponse> {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '' && value !== 'all') query.set(key, String(value));
  });
  const suffix = query.toString() ? `?${query.toString()}` : '';
  const res = await axios.get(resolveApiUrl(`/api/listing-composer/publish-queue${suffix}`));
  return res.data as PublishQueueListResponse;
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
