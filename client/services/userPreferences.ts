import axios from 'axios';

export interface Preferences {
  auto_social: boolean;
  social_handles: Record<string, string>;
}

const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function getPreferences(): Promise<Preferences> {
  const res = await axios.get<Preferences>(`${api}/api/user/preferences`, {
    headers: { 'X-User-Id': '1' },
  });
  return res.data;
}

export async function savePreferences(prefs: Preferences): Promise<Preferences> {
  const res = await axios.post<Preferences>(`${api}/api/user/preferences`, prefs, {
    headers: { 'X-User-Id': '1' },
  });
  return res.data;
}
