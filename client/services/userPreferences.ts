import axios from 'axios';
import { getAuthHeaders, resolveApiUrl } from './apiBase';

export interface Preferences {
  auto_social: boolean;
  social_handles: Record<string, string>;
  email_notifications: boolean;
  push_notifications: boolean;
  preferred_language: string;
  preferred_currency: string;
  timezone: string;
}

export async function getPreferences(): Promise<Preferences> {
  const res = await axios.get<Preferences>(resolveApiUrl('/api/user/preferences'), {
    headers: getAuthHeaders(),
  });
  return res.data;
}

export async function savePreferences(prefs: Preferences): Promise<Preferences> {
  const res = await axios.post<Preferences>(resolveApiUrl('/api/user/preferences'), prefs, {
    headers: getAuthHeaders(),
  });
  return res.data;
}
