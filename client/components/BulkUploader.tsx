import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { bulkCreate, BulkResult } from '../services/bulkUpload';

export default function BulkUploader() {
  const { t } = useTranslation('common');
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<BulkResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await bulkCreate(file);
      setResult(res);
    } catch (e) {
      setError(t('bulk.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{t('bulk.title')}</h1>
      <input
        aria-label={t('bulk.upload')}
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button
        type="button"
        className="bg-blue-600 text-white px-4 py-2"
        disabled={!file || loading}
        onClick={upload}
      >
        {t('bulk.upload')}
      </button>
      {loading && <p>{t('bulk.progress')}</p>}
      {result && <p>{t('bulk.success', { count: result.created })}</p>}
      {error && (
        <p role="alert" className="text-red-600">
          {error}
        </p>
      )}
      {result?.errors?.length ? (
        <ul>
          {result.errors.map((err, i) => (
            <li key={i}>{err}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
