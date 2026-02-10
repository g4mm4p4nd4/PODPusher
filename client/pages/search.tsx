import axios from 'axios';
import { GetServerSideProps } from 'next';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import { useTranslation } from 'next-i18next';
import { resolveApiUrl } from '../services/apiBase';

interface SearchResult {
  id: number;
  name: string;
  description: string;
  image_url: string;
  rating: number | null;
  tags: string[];
  category: string;
}

interface SearchResponse {
  items: SearchResult[];
  total: number;
}

interface SearchProps {
  categories: string[];
}

export default function SearchPage({ categories }: SearchProps) {
  const { t } = useTranslation('common');
  const router = useRouter();
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [tag, setTag] = useState('');
  const [rating, setRating] = useState(0);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (router.query.q) {
      setQ(String(router.query.q));
    }
  }, [router.query.q]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.get<SearchResponse>(resolveApiUrl('/api/search'), {
        params: {
          q: q || undefined,
          category: category || undefined,
          tag: tag || undefined,
          rating_min: rating || undefined,
        },
      });
      setResults(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('search.title')}</h1>
      <form onSubmit={submit} className="flex flex-wrap gap-2 items-end">
        <input
          className="border p-2 flex-grow"
          placeholder={t('search.keywordPlaceholder')}
          value={q}
          onChange={e => setQ(e.target.value)}
        />
        <select
          value={category}
          onChange={e => setCategory(e.target.value)}
          className="border p-2"
        >
          <option value="">{t('search.allCategories')}</option>
          {categories.map(c => (
            <option key={c} value={c}>
              {c.replace(/_/g, ' ')}
            </option>
          ))}
        </select>
        <input
          className="border p-2"
          placeholder={t('search.tagPlaceholder')}
          value={tag}
          onChange={e => setTag(e.target.value)}
        />
        <div className="flex flex-col items-start">
          <label className="text-sm">{t('search.rating')}</label>
          <input
            type="range"
            min="0"
            max="5"
            value={rating}
            onChange={e => setRating(parseInt(e.target.value, 10))}
          />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          {t('search.button')}
        </button>
      </form>
      {loading ? (
        <p>{t('search.loading')}</p>
      ) : results.length ? (
        <>
          <p>{t('search.results', { count: total })}</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {results.map(r => (
              <div key={r.id} className="border p-2 rounded">
                <img src={r.image_url} alt={r.name} loading="lazy" decoding="async" className="w-full h-32 object-cover mb-2" />
                <h3 className="font-semibold">{r.name}</h3>
                {r.rating && <p className="text-sm">{t('search.ratingLabel', { rating: r.rating })}</p>}
              </div>
            ))}
          </div>
        </>
      ) : (
        <p>{t('search.noResults')}</p>
      )}
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<SearchProps> = async () => {
  try {
    const res = await axios.get<{ name: string }[]>(resolveApiUrl('/product-categories'));
    return { props: { categories: res.data.map(c => c.name) } };
  } catch (err) {
    console.error(err);
    return { props: { categories: [] } };
  }
};
