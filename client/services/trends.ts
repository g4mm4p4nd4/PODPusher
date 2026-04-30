import axios from 'axios';

import { resolveApiUrl } from './apiBase';

export interface LiveTrendSignal {
  source: string;
  keyword: string;
  category: string;
  engagement_score: number;
  timestamp: string;
  method?: string;
  market_examples?: MarketExample[];
  provenance?: {
    source: string;
    is_estimated: boolean;
    updated_at: string;
    confidence: number;
  };
}

export interface MarketExample {
  title: string;
  keyword: string;
  source: string;
  source_url?: string | null;
  image_url?: string | null;
  engagement_score?: number;
  example_type?: string;
  provenance?: {
    source: string;
    is_estimated: boolean;
    updated_at: string;
    confidence: number;
  };
}

export type LiveTrendsByCategory = Record<string, LiveTrendSignal[]>;

export interface FetchLiveTrendsParams {
  category?: string;
  source?: string;
  lookbackHours?: number;
  limit?: number;
  page?: number;
  pageSize?: number;
  sortBy?: 'engagement_score' | 'timestamp' | 'keyword';
  sortOrder?: 'asc' | 'desc';
  includeMeta?: boolean;
}

export interface LiveTrendsMetaResponse {
  items_by_category: LiveTrendsByCategory;
  pagination: {
    page: number;
    page_size: number;
    per_group_limit: number;
    total: number;
    total_by_category: Record<string, number>;
    sort_by: string;
    sort_order: string;
  };
  provenance: {
    source: string;
    is_estimated: boolean;
    updated_at: string;
    confidence: number;
  };
}

export interface TrendRefreshStatus {
  last_started_at: string | null;
  last_finished_at: string | null;
  last_mode: string;
  sources_succeeded: string[];
  sources_failed: Record<string, string>;
  source_methods?: Record<string, string>;
  source_diagnostics?: Record<string, {
    status: string;
    method: string;
    collected: number;
    persisted: number;
    fallback_from?: string | null;
    fallback_to?: string | null;
    reason?: string | null;
    updated_at: string;
  }>;
  sources_blocked?: string[];
  failed_count?: number;
  fallback_count?: number;
  skipped_count?: number;
  blocked_count?: number;
  signals_collected: number;
  signals_persisted: number;
}

export async function fetchLiveTrends(
  params: FetchLiveTrendsParams & { includeMeta: true }
): Promise<LiveTrendsMetaResponse>;
export async function fetchLiveTrends(
  params?: FetchLiveTrendsParams
): Promise<LiveTrendsByCategory>;
export async function fetchLiveTrends(
  params: FetchLiveTrendsParams = {}
): Promise<LiveTrendsByCategory | LiveTrendsMetaResponse> {
  const { data } = await axios.get<LiveTrendsByCategory | LiveTrendsMetaResponse>(resolveApiUrl('/api/trends/live'), {
    params: {
      category: params.category,
      source: params.source,
      lookback_hours: params.lookbackHours ?? 72,
      limit: params.limit ?? 8,
      page: params.page,
      page_size: params.pageSize,
      sort_by: params.sortBy,
      sort_order: params.sortOrder,
      include_meta: params.includeMeta,
    },
  });
  return data;
}

export async function refreshLiveTrends(): Promise<TrendRefreshStatus> {
  const { data } = await axios.post<TrendRefreshStatus>(resolveApiUrl('/api/trends/refresh'));
  return data;
}

export async function fetchLiveTrendStatus(): Promise<TrendRefreshStatus> {
  const { data } = await axios.get<TrendRefreshStatus>(resolveApiUrl('/api/trends/live/status'));
  return data;
}
