import React, { useState, FormEvent } from 'react';
import axios from 'axios';

export type SearchResult = {
  id: number;
  image_url: string;
  rating: number | null;
  tags: string[];
  idea: string | null;
  term: string | null;
  category: string | null;
};

export default function SearchPage() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [q, setQ] = useState('');
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState('');
  const [ratingMin, setRatingMin] = useState('');
  const [ratingMax, setRatingMax] = useState('');

  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const res = await axios.get<SearchResult[]>(`${api}/api/search`, {
        params: {
          q: q || undefined,
          category: category || undefined,
          tags: tags ? tags.split(',').map(t => t.trim()) : undefined,
          rating_min: ratingMin ? Number(ratingMin) : undefined,
          rating_max: ratingMax ? Number(ratingMax) : undefined,
        },
      });
      setResults(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">Search</h1>
      <form onSubmit={submit} className="space-y-2">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="keyword"
          className="border p-2 w-full"
        />
        <input
          value={category}
          onChange={e => setCategory(e.target.value)}
          placeholder="category"
          className="border p-2 w-full"
        />
        <input
          value={tags}
          onChange={e => setTags(e.target.value)}
          placeholder="tags comma separated"
          className="border p-2 w-full"
        />
        <div className="flex gap-2">
          <input
            value={ratingMin}
            onChange={e => setRatingMin(e.target.value)}
            placeholder="min rating"
            className="border p-2 flex-1"
            type="number"
          />
          <input
            value={ratingMax}
            onChange={e => setRatingMax(e.target.value)}
            placeholder="max rating"
            className="border p-2 flex-1"
            type="number"
          />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          Search
        </button>
      </form>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {results.map(r => (
          <div key={r.id} className="border p-4 rounded" data-testid="result">
            <img src={r.image_url} alt="result" className="w-full h-40 object-cover mb-2" />
            <p className="font-semibold">{r.idea}</p>
            <p className="text-sm italic">{r.category}</p>
            <p className="text-sm">Rating: {r.rating ?? 'N/A'}</p>
            <p className="text-sm">Tags: {r.tags.join(', ')}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
