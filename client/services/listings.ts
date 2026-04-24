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
}

export async function saveDraft(data: DraftData): Promise<number> {
  const res = await axios.post(`${api}/api/listing-composer/drafts`, data);
  return res.data.id;
}

export async function loadDraft(id: number): Promise<DraftData> {
  const res = await axios.get(`${api}/api/listing-composer/drafts/${id}`);
  return res.data as DraftData;
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
