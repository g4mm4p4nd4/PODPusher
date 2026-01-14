import axios from 'axios';
import { resolveApiUrl } from './apiBase';

export interface Preferences {
  auto_social: boolean;
  social_handles: Record<string, string>;
}

export async function getPreferences(): Promise<Preferences> {
  const res = await axios.get<Preferences>(resolveApiUrl('/api/user/preferences'), {
    headers: { 'X-User-Id': '1' },
  });
  return res.data;
}

export async function savePreferences(prefs: Preferences): Promise<Preferences> {
  const res = await axios.post<Preferences>(resolveApiUrl('/api/user/preferences'), prefs, {
    headers: { 'X-User-Id': '1' },
  });
  return res.data;
}
