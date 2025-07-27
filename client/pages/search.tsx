import axios from 'axios';
import { GetServerSideProps } from 'next';
import { useState } from 'react';

interface SearchResult {
  id: number;
  name: string;
  description: string;
  image_url: string;
  rating: number | null;
  tags: string[];
  category: string;
}

interface SearchProps {
  categories: string[];
}

export default function SearchPage({ categories }: SearchProps) {
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [tag, setTag] = useState('');
  const [rating, setRating] = useState(0);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.get<SearchResult[]>(`${api}/api/search`, {
        params: {
          q: q || undefined,
          category: category || undefined,
          tag: tag || undefined,
          rating_min: rating || undefined,
        },
      });
      setResults(res.data);
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
          className="border p-2 flex-grow"
          placeholder="Keyword"
          value={q}
          onChange={e => setQ(e.target.value)}
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
          className="border p-2"
          placeholder="Tag"
          value={tag}
          onChange={e => setTag(e.target.value)}
        />
        <div className="flex flex-col items-start">
          <label className="text-sm">Rating</label>
          <input
            type="range"
            min="0"
            max="5"
            value={rating}
            onChange={e => setRating(parseInt(e.target.value, 10))}
          />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          Search
        </button>
      </form>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {results.map(r => (
            <div key={r.id} className="border p-2 rounded">
              <img src={r.image_url} alt={r.name} className="w-full h-32 object-cover mb-2" />
              <h3 className="font-semibold">{r.name}</h3>
              {r.rating && <p className="text-sm">Rating: {r.rating}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<SearchProps> = async () => {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  try {
    const res = await axios.get<{ name: string }[]>(`${api}/product-categories`);
    return { props: { categories: res.data.map(c => c.name) } };
  } catch (err) {
    console.error(err);
    return { props: { categories: [] } };
  }
};
