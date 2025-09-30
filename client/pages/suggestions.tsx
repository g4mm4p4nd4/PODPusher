import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { resolveApiUrl } from '../services/apiBase';

interface Suggestion {
  category: string;
  design_theme: string;
  suggestion: string;
}

export default function Suggestions() {
  const { t } = useTranslation('common');
  const [category, setCategory] = useState('');
  const [design, setDesign] = useState('');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  const fetchSuggestions = async () => {
    try {
      const res = await axios.get<Suggestion[]>(resolveApiUrl('/product-suggestions'), {
        params: {
          category: category || undefined,
          design: design || undefined,
        },
      });
      setSuggestions(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchSuggestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('suggestions.title')}</h1>
      <div className="flex gap-2">
        <input
          className="border p-2"
          placeholder={t('suggestions.category') as string}
          value={category}
          onChange={e => setCategory(e.target.value)}
        />
        <input
          className="border p-2"
          placeholder={t('suggestions.designTheme') as string}
          value={design}
          onChange={e => setDesign(e.target.value)}
        />
        <button onClick={fetchSuggestions} className="bg-blue-600 text-white px-4 py-2">
          {t('suggestions.fetch')}
        </button>
      </div>
      <ul className="space-y-2">
        {suggestions.map((s, idx) => (
          <li key={idx} className="border p-2 rounded">
            <strong>{s.category}</strong> ? {s.suggestion} ({s.design_theme})
          </li>
        ))}
      </ul>
    </div>
  );
}
