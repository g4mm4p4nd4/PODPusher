import axios from 'axios';
import { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { resolveApiUrl } from '../services/apiBase';

export default function Generate() {
  const { t } = useTranslation('common');
  const [term, setTerm] = useState('');
  const [result, setResult] = useState<any>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);
    try {
      const res = await axios.post(resolveApiUrl('/generate'), { term });
      setResult(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-2">{t('generate.title')}</h1>
      <form onSubmit={submit} className="flex gap-2">
        <input
          type="text"
          className="border p-2 flex-grow"
          placeholder={t('generate.placeholder')}
          value={term}
          onChange={e => setTerm(e.target.value)}
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          {t('generate.button')}
        </button>
      </form>
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
