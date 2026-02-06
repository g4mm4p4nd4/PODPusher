import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import {
  listOAuthCredentials,
  listOAuthProviders,
  OAuthCredentialSummary,
  OAuthProviderInfo,
} from '../services/oauth';

export type ProviderName = 'etsy' | 'printify' | 'stripe';

export interface ProviderStatus {
  provider: ProviderName;
  connected: boolean;
  accountName?: string | null;
  expiresAt?: Date | null;
  isExpiringSoon: boolean;
  isExpired: boolean;
}

interface ProviderContextValue {
  providers: OAuthProviderInfo[];
  credentials: Map<string, OAuthCredentialSummary>;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  isConnected: (provider: ProviderName) => boolean;
  getProviderStatus: (provider: ProviderName) => ProviderStatus;
  allRequiredConnected: () => boolean;
}

const ProviderContext = createContext<ProviderContextValue | null>(null);

const EXPIRY_WARNING_HOURS = 24;
const REQUIRED_PROVIDERS: ProviderName[] = ['etsy', 'printify'];

function checkExpiry(expiresAt: string | null | undefined): { isExpiringSoon: boolean; isExpired: boolean; date: Date | null } {
  if (!expiresAt) {
    return { isExpiringSoon: false, isExpired: false, date: null };
  }

  const expiry = new Date(expiresAt);
  const now = new Date();
  const hoursUntilExpiry = (expiry.getTime() - now.getTime()) / (1000 * 60 * 60);

  return {
    isExpiringSoon: hoursUntilExpiry > 0 && hoursUntilExpiry <= EXPIRY_WARNING_HOURS,
    isExpired: hoursUntilExpiry <= 0,
    date: expiry,
  };
}

export function ProviderProvider({ children }: { children: ReactNode }) {
  const [providers, setProviders] = useState<OAuthProviderInfo[]>([]);
  const [credentials, setCredentials] = useState<Map<string, OAuthCredentialSummary>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [providerList, credentialList] = await Promise.all([
        listOAuthProviders(),
        listOAuthCredentials(),
      ]);
      setProviders(providerList);
      const credMap = new Map<string, OAuthCredentialSummary>();
      credentialList.forEach((cred) => {
        credMap.set(cred.provider.toLowerCase(), cred);
      });
      setCredentials(credMap);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load provider status';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const isConnected = useCallback((provider: ProviderName): boolean => {
    const cred = credentials.get(provider.toLowerCase());
    if (!cred) return false;
    const { isExpired } = checkExpiry(cred.expires_at);
    return !isExpired;
  }, [credentials]);

  const getProviderStatus = useCallback((provider: ProviderName): ProviderStatus => {
    const cred = credentials.get(provider.toLowerCase());
    if (!cred) {
      return {
        provider,
        connected: false,
        accountName: null,
        expiresAt: null,
        isExpiringSoon: false,
        isExpired: false,
      };
    }
    const { isExpiringSoon, isExpired, date } = checkExpiry(cred.expires_at);
    return {
      provider,
      connected: !isExpired,
      accountName: cred.account_name,
      expiresAt: date,
      isExpiringSoon,
      isExpired,
    };
  }, [credentials]);

  const allRequiredConnected = useCallback((): boolean => {
    return REQUIRED_PROVIDERS.every((p) => isConnected(p));
  }, [isConnected]);

  const value: ProviderContextValue = {
    providers,
    credentials,
    loading,
    error,
    refresh,
    isConnected,
    getProviderStatus,
    allRequiredConnected,
  };

  return (
    <ProviderContext.Provider value={value}>
      {children}
    </ProviderContext.Provider>
  );
}

export function useProviders(): ProviderContextValue {
  const context = useContext(ProviderContext);
  if (!context) {
    throw new Error('useProviders must be used within a ProviderProvider');
  }
  return context;
}
