import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { useRouter } from 'next/router';
import { getPreferences, savePreferences, Preferences } from '../services/userPreferences';
import {
  authorizeOAuthProvider,
  deleteOAuthCredential,
  listOAuthCredentials,
  listOAuthProviders,
  OAuthCredentialSummary,
  OAuthProviderInfo,
} from '../services/oauth';
import OAuthProviderCard from './OAuthProviderCard';

interface CredentialMap {
  [key: string]: OAuthCredentialSummary;
}

interface FlashMessage {
  type: 'success' | 'error';
  message: string;
}

function computeRedirect(provider: string): string {
  if (typeof window === 'undefined') {
    return '';
  }
  const origin = window.location.origin.replace(/\/$/, '');
  return origin + '/oauth/callback/' + provider;
}

function mapCredentials(values: OAuthCredentialSummary[]): CredentialMap {
  const map: CredentialMap = {};
  values.forEach((item) => {
    map[item.provider] = item;
  });
  return map;
}

export default function SocialSettings() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [prefs, setPrefs] = useState<Preferences>({ auto_social: true, social_handles: {} });
  const [providers, setProviders] = useState<OAuthProviderInfo[]>([]);
  const [credentials, setCredentials] = useState<CredentialMap>({});
  const [oauthLoading, setOauthLoading] = useState(false);
  const [oauthError, setOauthError] = useState<string | null>(null);
  const [flash, setFlash] = useState<FlashMessage | null>(null);

  const formatProvider = useCallback(
    (provider: string) =>
      t(`settings.providers.${provider}`, {
        defaultValue: provider.charAt(0).toUpperCase() + provider.slice(1),
      }),
    [t],
  );

  useEffect(() => {
    getPreferences().then(setPrefs).catch((err) => console.error(err));
  }, []);

  const loadConnections = useCallback(async () => {
    try {
      setOauthLoading(true);
      const [providerList, credentialList] = await Promise.all([
        listOAuthProviders(),
        listOAuthCredentials(),
      ]);
      setProviders(providerList);
      setCredentials(mapCredentials(credentialList));
      setOauthError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : t('settings.error.load');
      setOauthError(message);
    } finally {
      setOauthLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadConnections();
  }, [loadConnections]);

  useEffect(() => {
    if (!flash) {
      return;
    }
    const timer = setTimeout(() => setFlash(null), 4000);
    return () => clearTimeout(timer);
  }, [flash]);

  const { oauth: oauthStatusRaw, provider: providerRaw, error: errorRaw } = router.query;

  useEffect(() => {
    if (!router.isReady) {
      return;
    }
    const status = Array.isArray(oauthStatusRaw) ? oauthStatusRaw[0] : oauthStatusRaw;
    const providerSlug = Array.isArray(providerRaw) ? providerRaw[0] : providerRaw;
    const errorText = Array.isArray(errorRaw) ? errorRaw[0] : errorRaw;
    if (!status) {
      return;
    }
    if (status === 'success' && providerSlug) {
      setFlash({
        type: 'success',
        message: t('settings.flash.linked', { provider: formatProvider(providerSlug) }),
      });
      loadConnections();
    } else if (status === 'error') {
      setFlash({
        type: 'error',
        message: errorText || t('settings.flash.error'),
      });
    }
    const nextQuery = { ...router.query } as Record<string, string | string[] | undefined>;
    delete nextQuery.oauth;
    delete nextQuery.provider;
    delete nextQuery.error;
    router.replace({ pathname: router.pathname, query: nextQuery }, undefined, { shallow: true });
  }, [
    router,
    router.isReady,
    oauthStatusRaw,
    providerRaw,
    errorRaw,
    t,
    formatProvider,
    loadConnections,
  ]);

  const updateHandle = (network: string, value: string) => {
    setPrefs({ ...prefs, social_handles: { ...prefs.social_handles, [network]: value } });
  };

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    await savePreferences(prefs);
  };

  const connect = async (provider: string) => {
    const redirect = computeRedirect(provider);
    try {
      setOauthLoading(true);
      setOauthError(null);
      setFlash(null);
      const response = await authorizeOAuthProvider(provider, redirect);
      if (response.authorization_url && typeof window !== 'undefined') {
        window.location.href = response.authorization_url;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : t('settings.error.oauth');
      setOauthError(message);
    } finally {
      setOauthLoading(false);
    }
  };

  const disconnect = async (provider: string) => {
    try {
      setOauthLoading(true);
      setOauthError(null);
      await deleteOAuthCredential(provider);
      await loadConnections();
      setFlash({
        type: 'success',
        message: t('settings.flash.removed', { provider: formatProvider(provider) }),
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : t('settings.error.disconnect');
      setOauthError(message);
    } finally {
      setOauthLoading(false);
    }
  };

  const connectionRows = useMemo(() => {
    return providers.map((provider) => {
      const summary = credentials[provider.provider];
      const connected = Boolean(summary);
      const label = formatProvider(provider.provider);
      return {
        name: provider.provider,
        label,
        connected,
        accountName: summary ? summary.account_name : null,
        expiresAt: summary ? summary.expires_at ?? null : null,
      };
    });
  }, [providers, credentials, formatProvider]);

  return (
    <div className="space-y-6">
      {flash && (
        <div
          className={`rounded border p-3 text-sm ${
            flash.type === 'success'
              ? 'border-green-200 bg-green-50 text-green-700'
              : 'border-red-200 bg-red-50 text-red-700'
          }`}
          role="status"
          aria-live="polite"
        >
          {flash.message}
        </div>
      )}

      <form onSubmit={save} className="space-y-4" aria-label={t('settings.title')}>
        <h1 className="text-2xl font-bold">{t('settings.title')}</h1>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={prefs.auto_social}
            onChange={(e) => setPrefs({ ...prefs, auto_social: e.target.checked })}
          />
          <span>{t('settings.auto')}</span>
        </label>
        <input
          className="border p-2 w-full"
          placeholder={t('settings.instagram')}
          value={prefs.social_handles.instagram || ''}
          onChange={(e) => updateHandle('instagram', e.target.value)}
        />
        <input
          className="border p-2 w-full"
          placeholder={t('settings.facebook')}
          value={prefs.social_handles.facebook || ''}
          onChange={(e) => updateHandle('facebook', e.target.value)}
        />
        <input
          className="border p-2 w-full"
          placeholder={t('settings.twitter')}
          value={prefs.social_handles.twitter || ''}
          onChange={(e) => updateHandle('twitter', e.target.value)}
        />
        <button type="submit" className="px-4 py-2 bg-blue-600 text-white">
          {t('settings.save')}
        </button>
      </form>

      <section aria-label="OAuth connections" className="space-y-3">
        <header className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">{t('settings.oauthTitle')}</h2>
          {oauthLoading && <span className="text-sm text-gray-500">{t('loading')}</span>}
        </header>
        {oauthError && (
          <div className="flex items-center gap-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            <span>{oauthError}</span>
            <button type="button" className="underline" onClick={loadConnections}>
              {t('settings.retry')}
            </button>
          </div>
        )}
        <ul className="space-y-2">
          {connectionRows.map((row) => (
            <li key={row.name}>
              <OAuthProviderCard
                provider={row.name}
                label={row.label}
                connected={row.connected}
                accountName={row.accountName}
                expiresAt={row.expiresAt}
                loading={oauthLoading}
                onConnect={() => connect(row.name)}
                onDisconnect={() => disconnect(row.name)}
              />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
