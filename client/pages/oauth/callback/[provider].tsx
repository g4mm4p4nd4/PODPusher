import { useRouter } from 'next/router';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { completeOAuthCallback } from '../../../services/oauth';

type Status = 'preparing' | 'working' | 'success' | 'error';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const { t } = useTranslation('common');
  const { provider: providerParam, code, state } = router.query;
  const providerSlug = Array.isArray(providerParam) ? providerParam[0] : providerParam;
  const [status, setStatus] = useState<Status>('preparing');
  const [message, setMessage] = useState<string>(t('oauth.preparing'));
  const [detail, setDetail] = useState<string>('');

  const providerLabel = useMemo(() => {
    if (typeof providerSlug !== 'string') {
      return '';
    }
    return t(`settings.providers.${providerSlug}`, {
      defaultValue: providerSlug.charAt(0).toUpperCase() + providerSlug.slice(1),
    });
  }, [providerSlug, t]);

  useEffect(() => {
    if (!router.isReady) {
      return;
    }
    if (typeof providerSlug !== 'string' || typeof code !== 'string' || typeof state !== 'string') {
      setStatus('error');
      setMessage(t('oauth.error'));
      setDetail(t('oauth.missingParams'));
      return;
    }

    let cancelled = false;
    let redirectTimer: ReturnType<typeof setTimeout> | null = null;
    const base = typeof window !== 'undefined' ? window.location.origin.replace(/\/$/, '') : '';
    const callbackPath = router.asPath.split('?')[0];
    const redirectUri = base + callbackPath;

    setStatus('working');
    setMessage(t('oauth.connecting'));
    setDetail('');

    completeOAuthCallback(providerSlug, code, state, redirectUri)
      .then((response) => {
        if (cancelled) {
          return;
        }
        const name = response.account_name || providerLabel || providerSlug;
        setStatus('success');
        setMessage(t('oauth.success', { provider: name }));
        setDetail(t('oauth.redirect'));
        redirectTimer = setTimeout(() => {
          if (!cancelled) {
            router.replace(
              {
                pathname: '/settings',
                query: { oauth: 'success', provider: providerSlug },
              },
              undefined,
              { shallow: true },
            );
          }
        }, 1500);
      })
      .catch((err) => {
        if (cancelled) {
          return;
        }
        const errorText = err instanceof Error ? err.message : t('oauth.error');
        setStatus('error');
        setMessage(t('oauth.error'));
        setDetail(errorText);
        redirectTimer = setTimeout(() => {
          if (!cancelled) {
            const query: Record<string, string> = { oauth: 'error', error: errorText };
            if (typeof providerSlug === 'string') {
              query.provider = providerSlug;
            }
            router.replace({ pathname: '/settings', query }, undefined, { shallow: true });
          }
        }, 2000);
      });

    return () => {
      cancelled = true;
      if (redirectTimer) {
        clearTimeout(redirectTimer);
      }
    };
  }, [router, router.isReady, router.asPath, providerSlug, code, state, providerLabel, t]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="max-w-md w-full bg-white shadow rounded p-6 space-y-4 text-center">
        <h1 className="text-2xl font-semibold">{t('oauth.title')}</h1>
        <p className="text-sm text-gray-700" role="status" aria-live="polite">
          {message}
        </p>
        {detail && <p className="text-xs text-gray-500 break-words">{detail}</p>}
        {status === 'error' && (
          <button
            type="button"
            className="mx-auto rounded border border-gray-300 px-4 py-2 text-sm"
            onClick={() => router.push('/settings')}
          >
            {t('oauth.return')}
          </button>
        )}
      </div>
    </div>
  );
}
