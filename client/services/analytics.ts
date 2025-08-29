import axios from 'axios';
import { SummaryRecord } from '../pages/analytics';

const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function fetchSummary(): Promise<SummaryRecord[]> {
  const res = await axios.get<SummaryRecord[]>(`${api}/analytics/summary`);
  return res.data;
}
