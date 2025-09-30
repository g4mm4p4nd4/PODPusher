import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { resolveApiUrl } from '../services/apiBase';

interface Category {
  name: string;
  items: string[];
}

export default function Categories() {
  const { t } = useTranslation('common');
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get<Category[]>(resolveApiUrl('/product-categories'));
        setCategories(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    load();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('categories.title')}</h1>
      {categories.map(cat => (
        <div key={cat.name}>
          <h2 className="text-xl font-semibold capitalize">{cat.name}</h2>
          <ul className="list-disc list-inside pl-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1">
            {cat.items.map(item => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
