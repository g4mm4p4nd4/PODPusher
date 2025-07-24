import { GetServerSideProps } from 'next';
import axios from 'axios';
import { useState } from 'react';

export type Suggestion = {
  category: string;
  design_theme: string;
  suggestion: string;
};

interface SuggestionsProps {
  suggestions: Suggestion[];
  categories: string[];
  designs: string[];
}

export default function Suggestions({ suggestions: initial, categories, designs }: SuggestionsProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>(initial);
  const [category, setCategory] = useState('');
  const [design, setDesign] = useState('');
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await axios.get<Suggestion[]>(`${api}/product-suggestions`, {
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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">Product Suggestions</h1>
      <form onSubmit={submit} className="flex flex-wrap gap-2 items-end">
        <div>
          <label className="block text-sm font-medium">Category</label>
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="border p-2 w-48"
          >
            <option value="">All</option>
            {categories.map(c => (
              <option key={c} value={c}>
                {c.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium">Design Theme</label>
          <select
            value={design}
            onChange={e => setDesign(e.target.value)}
            className="border p-2 w-48"
          >
            <option value="">All</option>
            {designs.map(d => (
              <option key={d} value={d}>
                {d.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          Fetch
        </button>
      </form>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {suggestions.map((s, idx) => (
          <div key={idx} className="border p-4 rounded">
            <h3 className="font-semibold capitalize">{s.category}</h3>
            <p className="text-sm italic">{s.design_theme.replace(/_/g, ' ')}</p>
            <p className="mt-2">{s.suggestion}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<SuggestionsProps> = async () => {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  try {
    const [sRes, cRes, dRes] = await Promise.all([
      axios.get<Suggestion[]>(`${api}/product-suggestions`),
      axios.get<{ name: string }[]>(`${api}/product-categories`),
      axios.get<{ name: string }[]>(`${api}/design-ideas`),
    ]);
    return {
      props: {
        suggestions: sRes.data,
        categories: cRes.data.map(c => c.name),
        designs: dRes.data.map(d => d.name),
      },
    };
  } catch (err) {
    console.error(err);
    return { props: { suggestions: [], categories: [], designs: [] } };
  }
};
