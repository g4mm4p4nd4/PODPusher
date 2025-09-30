import axios from 'axios';
import { resolveApiUrl } from './apiBase';

export interface OAuthProviderInfo {
  provider: string;
  auth_url: string;
  token_url: string;
  scope: string[];
  use_pkce: boolean;
}

export interface OAuthCredentialSummary {
  provider: string;
  expires_at?: string | null;
  scope?: string | null;
  account_id?: string | null;
  account_name?: string | null;
}

function buildAuthHeaders(token?: string) {
  if (!token) {
    return undefined;
  }
  return { Authorization: 'Bearer ' + token };
}

export async function listOAuthProviders(token?: string): Promise<OAuthProviderInfo[]> {
  const { data } = await axios.get<OAuthProviderInfo[]>(resolveApiUrl('/api/auth/providers'), {
    headers: buildAuthHeaders(token),
  });
  return data;
}

export async function listOAuthCredentials(token?: string): Promise<OAuthCredentialSummary[]> {
  const { data } = await axios.get<OAuthCredentialSummary[]>(resolveApiUrl('/api/auth/credentials'), {
    headers: buildAuthHeaders(token),
  });
  return data;
}

export async function authorizeOAuthProvider(
  provider: string,
  redirectUri: string,
  scope?: string[],
  token?: string,
): Promise<{ authorization_url: string }> {
  const { data } = await axios.post<{ authorization_url: string }>(
    resolveApiUrl('/api/auth/' + provider + '/authorize'),
    {
      redirect_uri: redirectUri,
      scope,
    },
    {
      headers: buildAuthHeaders(token),
    },
  );
  return data;
}

export async function completeOAuthCallback(
  provider: string,
  code: string,
  state: string,
  redirectUri?: string,
  token?: string,
): Promise<{ provider: string; account_name?: string | null }> {
  const { data } = await axios.post(
    resolveApiUrl('/api/auth/' + provider + '/callback'),
    {
      code,
      state,
      redirect_uri: redirectUri,
    },
    {
      headers: buildAuthHeaders(token),
    },
  );
  return data;
}

export async function deleteOAuthCredential(provider: string, token?: string): Promise<void> {
  await axios.delete(resolveApiUrl('/api/auth/credentials/' + provider), {
    headers: buildAuthHeaders(token),
  });
}
