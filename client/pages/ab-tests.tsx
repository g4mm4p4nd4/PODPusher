import axios from 'axios';
import { useState } from 'react';

interface Variant {
  title: string;
  description: string;
  tags: string;
}

export default function AbTests() {
  const [variantA, setVariantA] = useState<Variant>({ title: '', description: '', tags: '' });
  const [variantB, setVariantB] = useState<Variant>({ title: '', description: '', tags: '' });
  const [test, setTest] = useState<any | null>(null);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await axios.post(`${api}/api/ab_tests`, {
      variant_a: { ...variantA, tags: variantA.tags.split(',').map(t => t.trim()).filter(Boolean) },
      variant_b: { ...variantB, tags: variantB.tags.split(',').map(t => t.trim()).filter(Boolean) },
    });
    const id = res.data.id;
    const metrics = await axios.get(`${api}/api/ab_tests/${id}`);
    setTest(metrics.data);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">A/B Tests</h1>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block">Title A</label>
          <input aria-label="Title A" className="border" value={variantA.title} onChange={e => setVariantA({ ...variantA, title: e.target.value })} />
        </div>
        <div>
          <label className="block">Description A</label>
          <textarea className="border" value={variantA.description} onChange={e => setVariantA({ ...variantA, description: e.target.value })} />
        </div>
        <div>
          <label className="block">Tags A</label>
          <input className="border" value={variantA.tags} onChange={e => setVariantA({ ...variantA, tags: e.target.value })} />
        </div>
        <div>
          <label className="block">Title B</label>
          <input aria-label="Title B" className="border" value={variantB.title} onChange={e => setVariantB({ ...variantB, title: e.target.value })} />
        </div>
        <div>
          <label className="block">Description B</label>
          <textarea className="border" value={variantB.description} onChange={e => setVariantB({ ...variantB, description: e.target.value })} />
        </div>
        <div>
          <label className="block">Tags B</label>
          <input className="border" value={variantB.tags} onChange={e => setVariantB({ ...variantB, tags: e.target.value })} />
        </div>
        <button type="submit" className="bg-blue-500 text-white px-2">Create Test</button>
      </form>
      {test && (
        <div>
          <h2 className="font-semibold">Test ID: {test.id}</h2>
          {test.variants.map((v: any) => (
            <div key={v.variant} className="mt-2 p-2 border">
              <p>Variant {v.variant}</p>
              <p>Impressions: {v.impressions}</p>
              <p>Clicks: {v.clicks}</p>
              <p>Conversion: {v.conversion_rate.toFixed(2)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
