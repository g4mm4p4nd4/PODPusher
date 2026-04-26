import axios from 'axios';

import { getAuthHeaders, resolveApiUrl } from './apiBase';

async function request<T>(
  method: 'get' | 'post' | 'put' | 'patch',
  path: string,
  payload?: Record<string, unknown>
): Promise<T> {
  const response = await axios.request<T>({
    method,
    url: resolveApiUrl(path),
    data: payload,
    headers: getAuthHeaders(),
  });
  return response.data;
}

export function createAutomationJob(payload: Record<string, unknown>) {
  return request<Record<string, unknown>>('post', '/api/notifications/jobs', payload);
}

export function updateNotificationPreferences(payload: Record<string, unknown>) {
  return request<Record<string, unknown>>('put', '/api/notifications/preferences', payload);
}

export function updateNotificationRule(ruleId: number, payload: Record<string, unknown>) {
  return request<Record<string, unknown>>('patch', `/api/notifications/rules/${ruleId}`, payload);
}

export function saveSettingsLocalization(payload: Record<string, unknown>) {
  return request<Record<string, unknown>>('patch', '/api/settings/localization', payload);
}

export function createSettingsBrandProfile(payload: Record<string, unknown>) {
  return request<Record<string, unknown>>('post', '/api/settings/brand-profiles', payload);
}

export function setDefaultBrandProfile(profileId: number) {
  return request<Record<string, unknown>>('put', `/api/settings/brand-profiles/${profileId}/default`, {});
}

export function inviteSettingsUser(payload: Record<string, unknown>) {
  return request<Record<string, unknown>>('post', '/api/settings/users/invite', payload);
}

export function updateSettingsUserRole(memberId: number, payload: Record<string, unknown>) {
  return request<Record<string, unknown>>('patch', `/api/settings/users/${memberId}/role`, payload);
}

export function fetchUsageLedger() {
  return request<Record<string, unknown>>('get', '/api/settings/usage-ledger');
}

export function configureIntegration(provider: string, payload: Record<string, unknown>) {
  return request<Record<string, unknown>>(
    'post',
    `/api/settings/integrations/${provider}/configure`,
    payload
  );
}
