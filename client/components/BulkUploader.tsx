import { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { uploadBulk } from '../services/bulk';

interface ResultItem {
  status: 'ok' | 'error';
  message: string;
}

const toMessage = (value: unknown, fallback: string): string => {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : fallback;
  }

  if (value instanceof Error && value.message) {
    return value.message;
  }

  if (value && typeof value === 'object') {
    try {
      const serialized = JSON.stringify(value);
      if (serialized && serialized !== '{}' && serialized !== '[]') {
        return serialized;
      }
    } catch {
      /* noop */
    }
  }

  if (value != null) {
    const str = String(value).trim();
    if (str.length > 0 && str !== '[object Object]') {
      return str;
    }
  }

  return fallback;
};

export default function BulkUploader() {
  const { t } = useTranslation('common');
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<ResultItem[]>([]);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setResults([]);
    try {
      const data = await uploadBulk(file);
      const successes: ResultItem[] = (data.created || []).map((c: any) => ({
        status: 'ok',
        message: toMessage(
          c?.product?.title ?? c?.product?.name,
          t('bulk.success')
        ),
      }));
      const errs: ResultItem[] = (data.errors || []).map((e: any) => ({
        status: 'error',
        message: toMessage(e?.error, t('bulk.error')),
      }));
      setResults([...successes, ...errs]);
    } catch (err: any) {
      setResults([
        {
          status: 'error',
          message: toMessage(err?.message ?? err, t('bulk.error')),
        },
      ]);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">{t('bulk.title')}</h1>
      <input type="file" accept=".csv,.json" onChange={handleFile} />
      {uploading && <p>{t('bulk.uploading')}</p>}
      <ul className="space-y-1">
        {results.map((r, i) => (
          <li key={i} className={r.status === 'ok' ? 'text-green-600' : 'text-red-600'}>
            {r.message}
          </li>
        ))}
      </ul>
    </div>
  );
}
