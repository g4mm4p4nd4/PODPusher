import axios from 'axios';
import { useEffect, useState } from 'react';
import StarRating from '../../components/StarRating';
import Layout from '../../components/Layout';

interface Product {
  id: number;
  image_url: string;
  rating?: number | null;
  tags?: string | null;
  flagged: boolean;
}

export default function ReviewPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    const load = async () => {
      const res = await axios.get<Product[]>(`${api}/api/images/review`);
      setProducts(res.data);
    };
    load();
  }, [api]);

  const update = async (p: Product) => {
    await axios.post(`${api}/api/images/review/${p.id}`, {
      rating: p.rating,
      tags: p.tags ? p.tags.split(',').map(t => t.trim()) : [],
      flagged: p.flagged,
    });
  };

  return (
    <Layout>
      <h1 className="text-2xl font-bold mb-4">Image Reviews</h1>
      <div className="grid gap-4" data-testid="image-list">
        {products.map(p => (
          <div key={p.id} className="border p-4 flex gap-4 items-center">
            <img src={p.image_url} alt="product" className="w-24 h-24 object-cover" />
            <div className="flex-1 space-y-2">
              <StarRating value={p.rating || 0} onChange={v => setProducts(ps => ps.map(pr => (pr.id === p.id ? { ...pr, rating: v } : pr)))} />
              <input
                type="text"
                className="border p-1 w-full"
                placeholder="tags comma separated"
                value={p.tags || ''}
                onChange={e => setProducts(ps => ps.map(pr => (pr.id === p.id ? { ...pr, tags: e.target.value } : pr)))}
              />
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={p.flagged}
                  onChange={e => setProducts(ps => ps.map(pr => (pr.id === p.id ? { ...pr, flagged: e.target.checked } : pr)))}
                />
                Flagged
              </label>
              <button className="bg-blue-600 text-white px-2 py-1" onClick={() => update(p)} data-testid="save-btn">
                Save
              </button>
            </div>
          </div>
        ))}
      </div>
    </Layout>
  );
}
