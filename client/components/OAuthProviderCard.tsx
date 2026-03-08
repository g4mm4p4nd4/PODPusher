import React, { useMemo } from 'react';
import { useTranslation } from 'next-i18next';

interface OAuthProviderCardProps {
  provider: string;
  label: string;
  connected: boolean;
  accountName?: string | null;
  expiresAt?: string | null;
  onConnect: () => void;
  onDisconnect: () => void;
  loading?: boolean;
}

function computeExpiryMessage(expiresAt: string | null | undefined, t: (key: string, options?: Record<string, unknown>) => string) {
  if (!expiresAt) {
    return null;
  }
  const expiryDate = new Date(expiresAt);
  if (Number.isNaN(expiryDate.getTime())) {
    return null;
  }
  const diffMs = expiryDate.getTime() - Date.now();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays < 0) {
    return t('settings.status.expired');
  }
  if (diffDays === 0) {
    return t('settings.status.expiresToday');
  }
  return t('settings.status.expiresIn', { count: diffDays });
}

export default function OAuthProviderCard({
  provider,
  label,
  connected,
  accountName,
  expiresAt,
  onConnect,
  onDisconnect,
  loading,
}: OAuthProviderCardProps) {
  const { t } = useTranslation('common');
  const expiryMessage = useMemo(() => computeExpiryMessage(expiresAt, t), [expiresAt, t]);

  return (
    <div className="flex items-center justify-between gap-4 rounded border p-4 shadow-sm">
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <span className="text-base font-semibold capitalize">{label}</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${connected ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-700'}`}
          >
            {connected ? t('settings.status.connected') : t('settings.status.disconnected')}
          </span>
        </div>
        {connected ? (
          <p className="text-sm text-gray-700">
            {t('settings.connectedAs')} {accountName || t('settings.pendingAccount')}
          </p>
        ) : (
          <p className="text-sm text-gray-600">{t('settings.notConnected')}</p>
        )}
        {connected && expiryMessage && (
          <p className="text-xs text-gray-500">{expiryMessage}</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {connected ? (
          <button
            type="button"
            className="rounded border px-3 py-1 text-sm"
            onClick={onDisconnect}
            disabled={loading}
          >
            {t('settings.disconnect')}
          </button>
        ) : (
          <button
            type="button"
            className="rounded bg-green-600 px-3 py-1 text-sm text-white disabled:opacity-60"
            onClick={onConnect}
            disabled={loading}
          >
            {t('settings.connect')}
          </button>
        )}
      </div>
    </div>
  );
}
