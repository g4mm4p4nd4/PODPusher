import axios from 'axios';

const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export interface UserProfile {
  plan: string;
  quota_used: number;
  quota_limit: number | null;
}

export const quotaRefreshEvent = 'quota:refresh';
export const imageGeneratedEvent = 'image:generated';

const dispatchEvent = (name: string) => {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(name));
  }
};

export async function fetchCurrentUser(): Promise<UserProfile> {
  const res = await axios.get<UserProfile>(`${api}/api/user/me`, {
    headers: { 'X-User-Id': '1' },
  });
  return res.data;
}

export async function incrementQuota(count: number): Promise<UserProfile> {
  const res = await axios.post<UserProfile>(
    `${api}/api/user/me`,
    { count },
    { headers: { 'X-User-Id': '1' } }
  );
  dispatchEvent(quotaRefreshEvent);
  return res.data;
}

export function notifyImageGenerated(): void {
  dispatchEvent(imageGeneratedEvent);
}

export function triggerQuotaRefresh(): void {
  dispatchEvent(quotaRefreshEvent);
}
