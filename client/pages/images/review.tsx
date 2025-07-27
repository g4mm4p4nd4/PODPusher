import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';

interface Product {
  id: number;
  name: string;
  image_url: string;
  rating?: number | null;
  tags?: string[] | null;
  flagged?: boolean | null;
}

export default function ImageReview() {
  const { t } = useTranslation('common');
  const [products, setProducts] = useState<Product[]>([]);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get<Product[]>(`${api}/api/images/review`);
        setProducts(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, [api]);

  const update = async (id: number, changes: Partial<Product>) => {
    try {
      const res = await axios.post<Product>(`${api}/api/images/review/${id}`, changes);
      setProducts(p => p.map(prod => (prod.id === id ? res.data : prod)));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('review.title')}</h1>
      {products.length === 0 && <p>{t('review.noProducts')}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {products.map(p => (
          <div key={p.id} className="border p-4 rounded space-y-2">
            <img src={p.image_url} alt={p.name} className="w-full h-auto" />
            <div>
              <label className="block text-sm font-medium">{t('review.rating')}</label>
              <select
                data-testid={`rating-${p.id}`}
                className="border p-2 w-full"
                value={p.rating ?? ''}
                onChange={e => update(p.id, { rating: Number(e.target.value) })}
              >
                <option value="">{t('review.unrated')}</option>
                {[1, 2, 3, 4, 5].map(n => (
                  <option key={n} value={n}>
                    {t('review.stars', { count: n })}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium">{t('review.tags')}</label>
              <input
                data-testid={`tags-${p.id}`}
                type="text"
                className="border p-2 w-full"
                value={(p.tags ?? []).join(', ')}
                onChange={e =>
                  update(p.id, {
                    tags: e.target.value
                      .split(',')
                      .map(t => t.trim())
                      .filter(Boolean),
                  })
                }
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                data-testid={`flag-${p.id}`}
                type="checkbox"
                checked={p.flagged ?? false}
                onChange={e => update(p.id, { flagged: e.target.checked })}
              />
              <span className="text-sm">{t('review.flag')}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
