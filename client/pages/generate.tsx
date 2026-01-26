import axios from 'axios';
import { useState } from 'react';
import { useTranslation } from 'next-i18next';
import Link from 'next/link';
import { resolveApiUrl } from '../services/apiBase';
import { useProviders } from '../contexts/ProviderContext';

function ConnectionWarning() {
  const { t } = useTranslation('common');
  const { getProviderStatus } = useProviders();

  const etsyStatus = getProviderStatus('etsy');
  const printifyStatus = getProviderStatus('printify');

  const missingProviders: string[] = [];
  if (!etsyStatus.connected) missingProviders.push('Etsy');
  if (!printifyStatus.connected) missingProviders.push('Printify');

  if (missingProviders.length === 0) return null;

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        <svg className="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div className="flex-1">
          <h3 className="font-medium text-yellow-800">
            {t('generate.connectionRequired', 'Connection Required')}
          </h3>
          <p className="text-sm text-yellow-700 mt-1">
            {t('generate.connectProviders', 'To generate and publish listings, please connect the following accounts: {{providers}}', {
              providers: missingProviders.join(', '),
            })}
          </p>
          <Link
            href="/settings"
            className="inline-block mt-2 text-sm font-medium text-yellow-800 underline hover:text-yellow-900"
          >
            {t('generate.goToSettings', 'Go to Settings')}
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function Generate() {
  const { t } = useTranslation('common');
  const { allRequiredConnected, loading: providersLoading } = useProviders();
  const [term, setTerm] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canGenerate = allRequiredConnected();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canGenerate) return;

    setResult(null);
    setError(null);
    setLoading(true);

    try {
      const res = await axios.post(resolveApiUrl('/generate'), { term });
      setResult(res.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Generation failed';
      setError(message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (providersLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold mb-2">{t('generate.title')}</h1>
        <div className="animate-pulse">
          <div className="h-10 bg-gray-200 rounded w-full mb-4"></div>
          <div className="h-10 bg-gray-200 rounded w-32"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-2">{t('generate.title')}</h1>

      <ConnectionWarning />

      <form onSubmit={submit} className="flex gap-2">
        <input
          type="text"
          className="border p-2 flex-grow rounded"
          placeholder={t('generate.placeholder')}
          value={term}
          onChange={e => setTerm(e.target.value)}
          disabled={!canGenerate || loading}
        />
        <button
          type="submit"
          disabled={!canGenerate || loading || !term.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700"
        >
          {loading ? t('generate.generating', 'Generating...') : t('generate.button')}
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {result && (
        <div className="bg-gray-100 p-4 rounded">
          <pre className="whitespace-pre-wrap text-sm">
{JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
