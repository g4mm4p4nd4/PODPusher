import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import { getApiBase } from './apiBase';

/**
 * HTTP client with standardized error handling, retry logic, and rate limit awareness.
 *
 * Owner: Frontend-Coder (per DEVELOPMENT_PLAN.md Task 2.1.5, 2.2.3)
 * Reference: FC Error Handling, BC-08 Rate Limiting
 */

export interface APIErrorResponse {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  request_id: string;
}

export class APIRequestError extends Error {
  code: string;
  statusCode: number;
  requestId: string;
  details?: Record<string, unknown>;
  retryAfter?: number;

  constructor(
    message: string,
    code: string,
    statusCode: number,
    requestId: string,
    details?: Record<string, unknown>,
    retryAfter?: number,
  ) {
    super(message);
    this.name = 'APIRequestError';
    this.code = code;
    this.statusCode = statusCode;
    this.requestId = requestId;
    this.details = details;
    this.retryAfter = retryAfter;
  }

  get isRateLimited(): boolean {
    return this.statusCode === 429;
  }

  get isUnauthorized(): boolean {
    return this.statusCode === 401;
  }

  get isQuotaExceeded(): boolean {
    return this.statusCode === 402 || this.code === 'QUOTA_EXCEEDED';
  }

  get isServerError(): boolean {
    return this.statusCode >= 500;
  }
}

/** Rate limit state tracking for UI display. */
export interface RateLimitState {
  isLimited: boolean;
  retryAfter: number;
  remaining: number;
  limit: number;
}

let _rateLimitState: RateLimitState = {
  isLimited: false,
  retryAfter: 0,
  remaining: Infinity,
  limit: Infinity,
};

let _rateLimitListeners: Array<(state: RateLimitState) => void> = [];

export function getRateLimitState(): RateLimitState {
  return { ..._rateLimitState };
}

export function onRateLimitChange(listener: (state: RateLimitState) => void): () => void {
  _rateLimitListeners.push(listener);
  return () => {
    _rateLimitListeners = _rateLimitListeners.filter((l) => l !== listener);
  };
}

function _notifyRateLimitListeners(): void {
  const state = { ..._rateLimitState };
  _rateLimitListeners.forEach((l) => l(state));
}

function _updateRateLimitFromHeaders(headers: Record<string, string>): void {
  const limit = parseInt(headers['x-ratelimit-limit'] || '', 10);
  const remaining = parseInt(headers['x-ratelimit-remaining'] || '', 10);
  const retryAfter = parseInt(headers['retry-after'] || '', 10);

  if (!isNaN(limit)) _rateLimitState.limit = limit;
  if (!isNaN(remaining)) _rateLimitState.remaining = remaining;
  if (!isNaN(retryAfter) && retryAfter > 0) {
    _rateLimitState.isLimited = true;
    _rateLimitState.retryAfter = retryAfter;
    _notifyRateLimitListeners();

    // Auto-clear after countdown
    setTimeout(() => {
      _rateLimitState.isLimited = false;
      _rateLimitState.retryAfter = 0;
      _notifyRateLimitListeners();
    }, retryAfter * 1000);
  } else {
    _rateLimitState.isLimited = false;
  }
}

/** Create a configured HTTP client with error handling and retry. */
function createHttpClient(): AxiosInstance {
  const client = axios.create({
    baseURL: getApiBase(),
    timeout: 30000,
  });

  // Response interceptor for error handling and rate limit tracking
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      _updateRateLimitFromHeaders(response.headers as Record<string, string>);
      return response;
    },
    async (error: AxiosError<APIErrorResponse>) => {
      if (error.response) {
        const { status, data, headers } = error.response;
        _updateRateLimitFromHeaders(headers as Record<string, string>);

        const apiError = new APIRequestError(
          data?.message || error.message || 'Request failed',
          data?.code || 'UNKNOWN_ERROR',
          status,
          data?.request_id || '',
          data?.details,
          parseInt(headers?.['retry-after'] || '', 10) || undefined,
        );

        return Promise.reject(apiError);
      }

      // Network error (no response)
      return Promise.reject(
        new APIRequestError(
          'Network error — please check your connection',
          'NETWORK_ERROR',
          0,
          '',
        ),
      );
    },
  );

  return client;
}

/** Retry a request with exponential backoff. */
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000,
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));

      if (err instanceof APIRequestError) {
        // Don't retry client errors (4xx) except rate limits
        if (err.statusCode >= 400 && err.statusCode < 500 && err.statusCode !== 429) {
          throw err;
        }

        // Use server-provided retry-after if available
        if (err.retryAfter && attempt < maxRetries) {
          await new Promise((r) => setTimeout(r, err.retryAfter! * 1000));
          continue;
        }
      }

      if (attempt < maxRetries) {
        const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 500;
        await new Promise((r) => setTimeout(r, delay));
      }
    }
  }

  throw lastError!;
}

export const httpClient = createHttpClient();

export default httpClient;
