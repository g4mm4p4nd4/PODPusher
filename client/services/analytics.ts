import axios from 'axios';

export interface TrendingKeyword {
  term: string;
  clicks: number;
}

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function fetchTrendingKeywords(): Promise<TrendingKeyword[]> {
  const url = apiBase ? `${apiBase}/api/analytics` : '/api/analytics';
  const res = await axios.get<TrendingKeyword[]>(url);
  return res.data;
}
