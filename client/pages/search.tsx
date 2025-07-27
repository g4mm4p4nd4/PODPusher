import axios from 'axios';
import { useEffect, useState } from 'react';

interface Product {
  id: number;
  name: string;
  description: string;
  category: string;
  image_url: string;
  rating: number | null;
  tags: string[];
}

export default function Search() {
  const [keyword, setKeyword] = useState('');
  const [category, setCategory] = useState('');
  const [tag, setTag] = useState('');
  const [rating, setRating] = useState(0);
  const [results, setResults] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    axios
      .get<{ name: string }[]>(`${api}/product-categories`)
      .then(res => setCategories(res.data.map(c => c.name)))
      .catch(err => console.error(err));
  }, [api]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.get(`${api}/api/search`, {
        params: {
          q: keyword || undefined,
          category: category || undefined,
          tag: tag || undefined,
          rating_min: rating || undefined,
        },
      });
      setResults(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">Search</h1>
      <form onSubmit={submit} className="flex flex-wrap gap-2 items-end">
        <input
          type="text"
          className="border p-2 flex-grow"
          placeholder="Keyword"
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
        />
        <select
          value={category}
          onChange={e => setCategory(e.target.value)}
          className="border p-2"
        >
          <option value="">All Categories</option>
          {categories.map(c => (
            <option key={c} value={c}>
              {c.replace(/_/g, ' ')}
            </option>
          ))}
        </select>
        <input
          type="text"
          className="border p-2"
          placeholder="Tag"
          value={tag}
          onChange={e => setTag(e.target.value)}
        />
        <input
          type="range"
          min="0"
          max="5"
          value={rating}
          onChange={e => setRating(Number(e.target.value))}
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          Search
        </button>
      </form>
      {loading && <p>Loading...</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {results.map(r => (
          <div key={r.id} className="border p-4 rounded space-y-2">
            <img src={r.image_url} alt={r.name} className="w-full h-auto" />
            <h3 className="font-semibold">{r.name}</h3>
            <p className="text-sm italic">{r.category}</p>
            <p className="text-sm">{r.description}</p>
            <p className="text-sm">Rating: {r.rating ?? 'N/A'}</p>
            <div className="flex flex-wrap gap-1">
              {r.tags.map(t => (
                <span key={t} className="text-xs bg-gray-200 rounded px-1">
                  {t}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
