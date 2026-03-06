import axios from 'axios';

import { resolveApiUrl } from './apiBase';

export interface LiveTrendSignal {
  source: string;
  keyword: string;
  engagement_score: number;
  timestamp: string;
}

export type LiveTrendsByCategory = Record<string, LiveTrendSignal[]>;

export interface FetchLiveTrendsParams {
  category?: string;
  source?: string;
  lookbackHours?: number;
  limit?: number;
}

export interface TrendRefreshStatus {
  last_started_at: string | null;
  last_finished_at: string | null;
  last_mode: string;
  sources_succeeded: string[];
  sources_failed: Record<string, string>;
  signals_collected: number;
  signals_persisted: number;
}

export async function fetchLiveTrends(
  params: FetchLiveTrendsParams = {}
): Promise<LiveTrendsByCategory> {
  const { data } = await axios.get<LiveTrendsByCategory>(resolveApiUrl('/api/trends/live'), {
    params: {
      category: params.category,
      source: params.source,
      lookback_hours: params.lookbackHours ?? 72,
      limit: params.limit ?? 8,
    },
  });
  return data;
}

export async function refreshLiveTrends(): Promise<TrendRefreshStatus> {
  const { data } = await axios.post<TrendRefreshStatus>(resolveApiUrl('/api/trends/refresh'));
  return data;
}
