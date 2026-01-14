import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { completeOAuthCallback } from '../../../services/oauth';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const { provider, code, state } = router.query;
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    if (!router.isReady) {
      return;
    }
    if (typeof provider !== 'string' || typeof code !== 'string' || typeof state !== 'string') {
      setStatus('error');
      setMessage('Missing OAuth parameters.');
      return;
    }
    const base = typeof window !== 'undefined' ? window.location.origin.replace(/\/$/, '') : '';
    const callbackPath = router.asPath.split('?')[0];
    const redirectUri = base + callbackPath;
    setStatus('idle');
    setMessage('Connecting account...');
    completeOAuthCallback(provider, code, state, redirectUri)
      .then((response) => {
        setStatus('success');
        const name = response.account_name || 'account';
        setMessage('Linked ' + name + ' successfully.');
        setTimeout(() => {
          router.push('/settings');
        }, 1500);
      })
      .catch((err) => {
        setStatus('error');
        const text = err instanceof Error ? err.message : 'OAuth callback failed.';
        setMessage(text);
      });
  }, [router.isReady, provider, code, state, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="max-w-md w-full bg-white shadow rounded p-6 space-y-4 text-center">
        <h1 className="text-2xl font-semibold">OAuth Connection</h1>
        {status === 'idle' && <p>Preparing connection...</p>}
        {status === 'success' && <p className="text-green-600">{message}</p>}
        {status === 'error' && <p className="text-red-600">{message}</p>}
        {status === 'idle' && <p>{message}</p>}
      </div>
    </div>
  );
}
