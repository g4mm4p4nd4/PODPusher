import axios from 'axios';

export async function fetchTagSuggestions(title: string, description: string): Promise<string[]> {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const res = await axios.post<string[]>(`${api}/suggest-tags`, { title, description });
  return res.data;
}
