import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { ProviderName, ProviderStatus, useProviders } from '../contexts/ProviderContext';
import { authorizeOAuthProvider, deleteOAuthCredential } from '../services/oauth';

interface StatusBadgeProps {
  status: ProviderStatus;
}

function StatusBadge({ status }: StatusBadgeProps) {
  const { t } = useTranslation('common');

  if (status.isExpired) {
    return (
      <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
        {t('oauth.expired', 'Expired')}
      </span>
    );
  }

  if (status.isExpiringSoon) {
    return (
      <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
        {t('oauth.expiringSoon', 'Expiring Soon')}
      </span>
    );
  }

  if (status.connected) {
    return (
      <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
        {t('oauth.connected', 'Connected')}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
      {t('oauth.notConnected', 'Not Connected')}
    </span>
  );
}

interface ProviderLogoProps {
  provider: ProviderName;
}

function ProviderLogo({ provider }: ProviderLogoProps) {
  const logos: Record<ProviderName, string> = {
    etsy: '/icons/etsy.svg',
    printify: '/icons/printify.svg',
    stripe: '/icons/stripe.svg',
  };

  return (
    <div className="w-10 h-10 flex items-center justify-center bg-gray-100 rounded-lg">
      <span className="text-lg font-bold capitalize text-gray-600">
        {provider.charAt(0).toUpperCase()}
      </span>
    </div>
  );
}

interface OAuthConnectCardProps {
  provider: ProviderName;
  description?: string;
  onConnectionChange?: () => void;
}

export function OAuthConnectCard({ provider, description, onConnectionChange }: OAuthConnectCardProps) {
  const { t } = useTranslation('common');
  const { getProviderStatus, refresh } = useProviders();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);

  const status = getProviderStatus(provider);

  const computeRedirect = (): string => {
    if (typeof window === 'undefined') return '';
    const origin = window.location.origin.replace(/\/$/, '');
    return `${origin}/oauth/callback/${provider}`;
  };

  const handleConnect = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await authorizeOAuthProvider(provider, computeRedirect());
      if (response.authorization_url && typeof window !== 'undefined') {
        window.location.href = response.authorization_url;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start connection';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setLoading(true);
      setError(null);
      await deleteOAuthCredential(provider);
      await refresh();
      setShowDisconnectConfirm(false);
      onConnectionChange?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to disconnect';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    await handleConnect();
  };

  const formatExpiryDate = (date: Date | null | undefined): string => {
    if (!date) return '';
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <ProviderLogo provider={provider} />
          <div>
            <h3 className="font-semibold capitalize text-gray-900">{provider}</h3>
            {description && (
              <p className="text-sm text-gray-500">{description}</p>
            )}
            {status.connected && status.accountName && (
              <p className="text-sm text-gray-600">
                {t('oauth.connectedAs', 'Connected as')} {status.accountName}
              </p>
            )}
            {status.isExpiringSoon && status.expiresAt && (
              <p className="text-sm text-yellow-600">
                {t('oauth.expiresOn', 'Expires')}: {formatExpiryDate(status.expiresAt)}
              </p>
            )}
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}

      <div className="mt-4 flex gap-2">
        {!status.connected && (
          <button
            type="button"
            onClick={handleConnect}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? t('oauth.connecting', 'Connecting...') : t('oauth.connect', 'Connect')}
          </button>
        )}

        {status.connected && (
          <>
            {status.isExpiringSoon && (
              <button
                type="button"
                onClick={handleRefresh}
                disabled={loading}
                className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50"
              >
                {t('oauth.refresh', 'Refresh Connection')}
              </button>
            )}
            {!showDisconnectConfirm ? (
              <button
                type="button"
                onClick={() => setShowDisconnectConfirm(true)}
                disabled={loading}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                {t('oauth.disconnect', 'Disconnect')}
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">{t('oauth.confirmDisconnect', 'Are you sure?')}</span>
                <button
                  type="button"
                  onClick={handleDisconnect}
                  disabled={loading}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {t('oauth.yes', 'Yes')}
                </button>
                <button
                  type="button"
                  onClick={() => setShowDisconnectConfirm(false)}
                  disabled={loading}
                  className="px-3 py-1 border border-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-50"
                >
                  {t('oauth.cancel', 'Cancel')}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

interface OAuthConnectProps {
  onConnectionChange?: () => void;
}

export default function OAuthConnect({ onConnectionChange }: OAuthConnectProps) {
  const { t } = useTranslation('common');
  const { loading, error } = useProviders();

  const providerDescriptions: Record<ProviderName, string> = {
    etsy: t('oauth.etsyDesc', 'Publish listings to your Etsy shop'),
    printify: t('oauth.printifyDesc', 'Create products and manage inventory'),
    stripe: t('oauth.stripeDesc', 'Manage billing and subscriptions'),
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">{t('oauth.connectedAccounts', 'Connected Accounts')}</h2>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">{t('oauth.connectedAccounts', 'Connected Accounts')}</h2>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <div className="space-y-3">
        <OAuthConnectCard
          provider="etsy"
          description={providerDescriptions.etsy}
          onConnectionChange={onConnectionChange}
        />
        <OAuthConnectCard
          provider="printify"
          description={providerDescriptions.printify}
          onConnectionChange={onConnectionChange}
        />
        <OAuthConnectCard
          provider="stripe"
          description={providerDescriptions.stripe}
          onConnectionChange={onConnectionChange}
        />
      </div>
    </div>
  );
}
