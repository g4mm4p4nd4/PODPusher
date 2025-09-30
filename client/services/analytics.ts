import axios from 'axios';
import { resolveApiUrl } from './apiBase';

export interface TrendingKeyword {
  term: string;
  clicks: number;
}

export async function fetchTrendingKeywords(): Promise<TrendingKeyword[]> {
  const url = resolveApiUrl('/api/analytics');
  const res = await axios.get<TrendingKeyword[]>(url);
  return res.data;
}
