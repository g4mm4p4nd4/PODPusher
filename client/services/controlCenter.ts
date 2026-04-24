import axios from 'axios';

import { getAuthHeaders, resolveApiUrl } from './apiBase';

export type Provenance = {
  source: string;
  is_estimated: boolean;
  updated_at: string;
  confidence: number;
};

export type Metric = {
  label: string;
  value: number | string;
  delta?: number;
  unit?: string;
  sparkline?: number[];
  provenance?: Provenance;
  quota?: Record<string, unknown>;
};

export type DashboardResponse = Record<string, any>;

async function get<T = DashboardResponse>(path: string, params?: Record<string, unknown>): Promise<T> {
  const response = await axios.get<T>(resolveApiUrl(path), {
    headers: getAuthHeaders(),
    params,
  });
  return response.data;
}

async function post<T = DashboardResponse>(
  path: string,
  payload: Record<string, unknown>
): Promise<T> {
  const response = await axios.post<T>(resolveApiUrl(path), payload, {
    headers: getAuthHeaders(),
  });
  return response.data;
}

export function fetchOverview() {
  return get('/api/dashboard/overview');
}

export function fetchTrendInsights(params?: Record<string, unknown>) {
  return get('/api/trends/insights', params);
}

export function fetchSeasonalEvents(params?: Record<string, unknown>) {
  return get('/api/seasonal/events', params);
}

export function saveSeasonalEvent(name: string) {
  return post('/api/seasonal/events/save', { name });
}

export function fetchNicheSuggestions() {
  return get('/api/niches/suggestions');
}

export function saveBrandProfile(payload: Record<string, unknown>) {
  return post('/api/niches/profile', payload);
}

export function saveNiche(niche: string, score: number) {
  return post('/api/niches/saved', { niche, score });
}

export function fetchSearchInsights(params?: Record<string, unknown>) {
  return get('/api/search/insights', params);
}

export function saveSearch(payload: Record<string, unknown>) {
  return post('/api/search/saved', payload);
}

export function addToWatchlist(payload: Record<string, unknown>) {
  return post('/api/search/watchlist', payload);
}

export function generateListing(payload: Record<string, unknown>) {
  return post('/api/listing-composer/generate', payload);
}

export function scoreListing(payload: Record<string, unknown>) {
  return post('/api/listing-composer/score', payload);
}

export function checkListingCompliance(payload: Record<string, unknown>) {
  return post('/api/listing-composer/compliance', payload);
}

export function fetchABDashboard() {
  return get('/api/ab-tests/dashboard');
}

export function abAction(testId: number, action: 'pause' | 'duplicate' | 'end' | 'push-winner') {
  return post(`/api/ab-tests/${testId}/${action}`, {});
}

export function fetchNotificationsDashboard() {
  return get('/api/notifications/dashboard');
}

export function createNotificationRule(payload: Record<string, unknown>) {
  return post('/api/notifications/rules', payload);
}

export function fetchSettingsDashboard() {
  return get('/api/settings/dashboard');
}
