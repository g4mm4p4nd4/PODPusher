import axios from 'axios';
import { SummaryRecord } from '../pages/analytics';

const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function fetchSummary(eventType: string): Promise<SummaryRecord[]> {
  const res = await axios.get<SummaryRecord[]>(`${api}/analytics/summary`, {
    params: { event_type: eventType },
  });
  return res.data;
}

export async function logEvent(
  eventType: string,
  path: string,
  meta?: Record<string, any>,
): Promise<void> {
  try {
    await axios.post(`${api}/analytics/events`, {
      event_type: eventType,
      path,
      meta,
    });
  } catch (err) {
    // Swallow errors to avoid impacting UX
    console.error(err);
  }
}
