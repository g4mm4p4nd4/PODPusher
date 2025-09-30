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
