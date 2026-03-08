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

const DEFAULT_PREFS: Preferences = {
  auto_social: true,
  social_handles: {},
  email_notifications: true,
  push_notifications: false,
  preferred_language: 'en',
  preferred_currency: 'USD',
  timezone: 'UTC',
};

const PROVIDER_TRANSLATION_KEYS: Record<string, string> = {
  etsy: 'settings.providers.etsy',
  printify: 'settings.providers.printify',
  stripe: 'settings.providers.stripe',
};

/** Validates a social media handle: optional @, then 1-30 alphanumeric/underscore/dot chars. */
const HANDLE_REGEX = /^@?[a-zA-Z0-9_.]{1,30}$/;

function isValidHandle(value: string): boolean {
  return value === '' || HANDLE_REGEX.test(value);
}

export default function SocialSettings() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);
  const [providers, setProviders] = useState<OAuthProviderInfo[]>([]);
  const [credentials, setCredentials] = useState<CredentialMap>({});
  const [oauthLoading, setOauthLoading] = useState(false);
  const [oauthError, setOauthError] = useState<string | null>(null);
  const [flash, setFlash] = useState<FlashMessage | null>(null);
  const [handleErrors, setHandleErrors] = useState<Record<string, string>>({});

  const formatProvider = useCallback(
    (provider: string) => t(PROVIDER_TRANSLATION_KEYS[provider] ?? 'settings.providers.unknown'),
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
    if (value && !isValidHandle(value)) {
      setHandleErrors((prev) => ({ ...prev, [network]: t('settings.invalidHandle') }));
    } else {
      setHandleErrors((prev) => {
        const next = { ...prev };
        delete next[network];
        return next;
      });
    }
  };

  const hasHandleErrors = Object.keys(handleErrors).length > 0;

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    if (hasHandleErrors) return;
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
        <div>
          <input
            className={`border p-2 w-full${handleErrors.instagram ? ' border-red-500' : ''}`}
            placeholder={t('settings.instagram')}
            value={prefs.social_handles.instagram || ''}
            onChange={(e) => updateHandle('instagram', e.target.value)}
          />
          {handleErrors.instagram && <p className="text-sm text-red-600 mt-1">{handleErrors.instagram}</p>}
        </div>
        <div>
          <input
            className={`border p-2 w-full${handleErrors.facebook ? ' border-red-500' : ''}`}
            placeholder={t('settings.facebook')}
            value={prefs.social_handles.facebook || ''}
            onChange={(e) => updateHandle('facebook', e.target.value)}
          />
          {handleErrors.facebook && <p className="text-sm text-red-600 mt-1">{handleErrors.facebook}</p>}
        </div>
        <div>
          <input
            className={`border p-2 w-full${handleErrors.twitter ? ' border-red-500' : ''}`}
            placeholder={t('settings.twitter')}
            value={prefs.social_handles.twitter || ''}
            onChange={(e) => updateHandle('twitter', e.target.value)}
          />
          {handleErrors.twitter && <p className="text-sm text-red-600 mt-1">{handleErrors.twitter}</p>}
        </div>
        <div>
          <input
            className={`border p-2 w-full${handleErrors.tiktok ? ' border-red-500' : ''}`}
            placeholder={t('settings.tiktok')}
            value={prefs.social_handles.tiktok || ''}
            onChange={(e) => updateHandle('tiktok', e.target.value)}
          />
          {handleErrors.tiktok && <p className="text-sm text-red-600 mt-1">{handleErrors.tiktok}</p>}
        </div>

        <fieldset className="border rounded p-4 space-y-2">
          <legend className="text-lg font-semibold px-2">
            {t('settings.notificationChannels')}
          </legend>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={prefs.email_notifications}
              onChange={(e) => setPrefs({ ...prefs, email_notifications: e.target.checked })}
            />
            <span>{t('settings.emailNotifications')}</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={prefs.push_notifications}
              onChange={(e) => setPrefs({ ...prefs, push_notifications: e.target.checked })}
            />
            <span>{t('settings.pushNotifications')}</span>
          </label>
        </fieldset>

        <fieldset className="border rounded p-4 space-y-3">
          <legend className="text-lg font-semibold px-2">
            {t('settings.preferences')}
          </legend>
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('settings.defaultLanguage')}
            </label>
            <select
              className="border p-2 w-full rounded"
              value={prefs.preferred_language}
              onChange={(e) => setPrefs({ ...prefs, preferred_language: e.target.value })}
            >
              <option value="en">{t('settings.languages.en')}</option>
              <option value="es">{t('settings.languages.es')}</option>
              <option value="fr">{t('settings.languages.fr')}</option>
              <option value="de">{t('settings.languages.de')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('settings.currency')}
            </label>
            <select
              className="border p-2 w-full rounded"
              value={prefs.preferred_currency}
              onChange={(e) => setPrefs({ ...prefs, preferred_currency: e.target.value })}
            >
              <option value="USD">{t('settings.currencies.USD')}</option>
              <option value="EUR">{t('settings.currencies.EUR')}</option>
              <option value="GBP">{t('settings.currencies.GBP')}</option>
              <option value="CAD">{t('settings.currencies.CAD')}</option>
              <option value="AUD">{t('settings.currencies.AUD')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('settings.timezone')}
            </label>
            <select
              className="border p-2 w-full rounded"
              value={prefs.timezone}
              onChange={(e) => setPrefs({ ...prefs, timezone: e.target.value })}
            >
              <option value="UTC">{t('settings.timezones.utc')}</option>
              <option value="America/New_York">{t('settings.timezones.americaNewYork')}</option>
              <option value="America/Chicago">{t('settings.timezones.americaChicago')}</option>
              <option value="America/Denver">{t('settings.timezones.americaDenver')}</option>
              <option value="America/Los_Angeles">{t('settings.timezones.americaLosAngeles')}</option>
              <option value="Europe/London">{t('settings.timezones.europeLondon')}</option>
              <option value="Europe/Paris">{t('settings.timezones.europeParis')}</option>
              <option value="Asia/Tokyo">{t('settings.timezones.asiaTokyo')}</option>
              <option value="Australia/Sydney">{t('settings.timezones.australiaSydney')}</option>
            </select>
          </div>
        </fieldset>

        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">
          {t('settings.save')}
        </button>
      </form>

      <section aria-label={t('settings.oauthConnectionsAria')} className="space-y-3">
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
