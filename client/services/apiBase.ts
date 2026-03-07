const DEFAULT_API_PORT = '8000';
const DEFAULT_USER_ID = '1';
const SESSION_TOKEN_KEY = 'pod.session.token';
const USER_ID_KEY = 'pod.user.id';

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '');
}

function getConfiguredApiBase(): string | null {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  return configured ? trimTrailingSlash(configured) : null;
}

function getBrowserApiBase(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const configuredPort = process.env.NEXT_PUBLIC_API_PORT?.trim() || DEFAULT_API_PORT;
  const { protocol, hostname, origin } = window.location;
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}:${configuredPort}`;
  }
  return trimTrailingSlash(origin);
}

export function getApiBase(): string {
  return getConfiguredApiBase() || getBrowserApiBase() || `http://localhost:${DEFAULT_API_PORT}`;
}

export function resolveApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${getApiBase()}${normalizedPath}`;
}

export function getCurrentUserId(): string {
  if (typeof window !== 'undefined') {
    const stored = window.localStorage.getItem(USER_ID_KEY)?.trim();
    if (stored) {
      return stored;
    }
  }
  return process.env.NEXT_PUBLIC_POD_USER_ID?.trim() || DEFAULT_USER_ID;
}

export function getStoredSessionToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const token = window.localStorage.getItem(SESSION_TOKEN_KEY)?.trim();
  return token || null;
}

export function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = getStoredSessionToken();
  const userId = getCurrentUserId();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (userId) {
    headers['X-User-Id'] = userId;
  }
  return headers;
}
