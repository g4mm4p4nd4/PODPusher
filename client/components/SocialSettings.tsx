import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { getPreferences, savePreferences, Preferences } from '../services/userPreferences';
import {
  authorizeOAuthProvider,
  deleteOAuthCredential,
  listOAuthCredentials,
  listOAuthProviders,
  OAuthCredentialSummary,
  OAuthProviderInfo,
} from '../services/oauth';

interface CredentialMap {
  [key: string]: OAuthCredentialSummary;
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

export default function SocialSettings() {
  const { t } = useTranslation('common');
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);
  const [providers, setProviders] = useState<OAuthProviderInfo[]>([]);
  const [credentials, setCredentials] = useState<CredentialMap>({});
  const [oauthLoading, setOauthLoading] = useState(false);
  const [oauthError, setOauthError] = useState<string | null>(null);

  useEffect(() => {
    getPreferences().then(setPrefs).catch((err) => console.error(err));
  }, []);

  const loadConnections = async () => {
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
      const message = err instanceof Error ? err.message : 'Unable to load connections';
      setOauthError(message);
    } finally {
      setOauthLoading(false);
    }
  };

  useEffect(() => {
    loadConnections();
  }, []);

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
      const response = await authorizeOAuthProvider(provider, redirect);
      if (response.authorization_url && typeof window !== 'undefined') {
        window.location.href = response.authorization_url;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to start OAuth';
      setOauthError(message);
    }
  };

  const disconnect = async (provider: string) => {
    try {
      await deleteOAuthCredential(provider);
      await loadConnections();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to disconnect';
      setOauthError(message);
    }
  };

  const connectionRows = useMemo(() => {
    return providers.map((provider) => {
      const summary = credentials[provider.provider];
      const connected = Boolean(summary);
      return {
        name: provider.provider,
        connected,
        accountName: summary ? summary.account_name : null,
        expiresAt: summary ? summary.expires_at : null,
      };
    });
  }, [providers, credentials]);

  return (
    <div className="space-y-6">
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
        <input
          className="border p-2 w-full"
          placeholder={t('settings.tiktok')}
          value={prefs.social_handles.tiktok || ''}
          onChange={(e) => updateHandle('tiktok', e.target.value)}
        />

        {/* Notification Channel Preferences */}
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

        {/* Language, Currency, Timezone Preferences */}
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
              <option value="en">English</option>
              <option value="es">Espa&#241;ol</option>
              <option value="fr">Fran&#231;ais</option>
              <option value="de">Deutsch</option>
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
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (&euro;)</option>
              <option value="GBP">GBP (&pound;)</option>
              <option value="CAD">CAD ($)</option>
              <option value="AUD">AUD ($)</option>
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
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern (US)</option>
              <option value="America/Chicago">Central (US)</option>
              <option value="America/Denver">Mountain (US)</option>
              <option value="America/Los_Angeles">Pacific (US)</option>
              <option value="Europe/London">London</option>
              <option value="Europe/Paris">Paris / Berlin</option>
              <option value="Asia/Tokyo">Tokyo</option>
              <option value="Australia/Sydney">Sydney</option>
            </select>
          </div>
        </fieldset>

        <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">
          {t('settings.save')}
        </button>
      </form>

      <section aria-label="OAuth connections" className="space-y-3">
        <header className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">{t('settings.oauthTitle', 'Integrations')}</h2>
          {oauthLoading && <span className="text-sm text-gray-500">{t('loading', 'Loading...')}</span>}
        </header>
        {oauthError && <p className="text-sm text-red-600">{oauthError}</p>}
        <ul className="space-y-2">
          {connectionRows.map((row) => (
            <li key={row.name} className="flex items-center justify-between border p-3 rounded">
              <div>
                <p className="font-medium capitalize">{row.name}</p>
                {row.connected ? (
                  <p className="text-sm text-gray-600">
                    {t('settings.connectedAs', 'Connected as')} {row.accountName || t('settings.pendingAccount', 'Pending account info')}
                  </p>
                ) : (
                  <p className="text-sm text-gray-600">{t('settings.notConnected', 'Not connected')}</p>
                )}
              </div>
              <div className="flex gap-2">
                {row.connected ? (
                  <button type="button" className="px-3 py-1 border rounded" onClick={() => disconnect(row.name)}>
                    {t('settings.disconnect', 'Disconnect')}
                  </button>
                ) : (
                  <button type="button" className="px-3 py-1 bg-green-600 text-white rounded" onClick={() => connect(row.name)}>
                    {t('settings.connect', 'Connect')}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
