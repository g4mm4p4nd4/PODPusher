const FALLBACK_API_BASE = 'http://localhost:8000';

const stripTrailingSlash = (value: string): string => value.replace(/\/+$/, '');

export function getApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL;
  if (!configured) {
    return FALLBACK_API_BASE;
  }
  return stripTrailingSlash(configured);
}

export function resolveApiUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${getApiBase()}${normalizedPath}`;
}
