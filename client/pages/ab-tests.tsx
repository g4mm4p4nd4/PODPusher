import axios from 'axios';
import { useState } from 'react';

export type Metric = {
  variant_name: string;
  impressions: number;
  clicks: number;
  conversion_rate: number;
};

export default function AbTests() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [variantA, setVariantA] = useState('');
  const [variantB, setVariantB] = useState('');
  const [tagsA, setTagsA] = useState('');
  const [tagsB, setTagsB] = useState('');
  const [testId, setTestId] = useState<number | null>(null);
  const [metrics, setMetrics] = useState<Metric[] | null>(null);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const fetchMetrics = async (id: number) => {
    const res = await axios.get<Metric[]>(`${api}/ab_tests/${id}`);
    setMetrics(res.data);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await axios.post<{ id: number }>(`${api}/ab_tests`, {
      title,
      description,
      variant_a: variantA,
      variant_b: variantB,
      tags_a: tagsA.split(',').map(t => t.trim()).filter(Boolean),
      tags_b: tagsB.split(',').map(t => t.trim()).filter(Boolean),
    });
    setTestId(res.data.id);
    fetchMetrics(res.data.id);
  };

  const clickVariant = async (name: string) => {
    if (!testId) return;
    await axios.post(`${api}/ab_tests/${testId}/record_click`, null, {
      params: { variant: name },
    });
    fetchMetrics(testId);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">A/B Tests</h1>
      <form onSubmit={submit} className="space-y-2">
        <input
          className="border p-2 w-full"
          placeholder="Title"
          value={title}
          onChange={e => setTitle(e.target.value)}
        />
        <textarea
          className="border p-2 w-full"
          placeholder="Description"
          value={description}
          onChange={e => setDescription(e.target.value)}
        />
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex-1 space-y-1">
            <input
              className="border p-2 w-full"
              placeholder="Variant A"
              value={variantA}
              onChange={e => setVariantA(e.target.value)}
            />
            <input
              className="border p-2 w-full"
              placeholder="Tags A comma separated"
              value={tagsA}
              onChange={e => setTagsA(e.target.value)}
            />
          </div>
          <div className="flex-1 space-y-1">
            <input
              className="border p-2 w-full"
              placeholder="Variant B"
              value={variantB}
              onChange={e => setVariantB(e.target.value)}
            />
            <input
              className="border p-2 w-full"
              placeholder="Tags B comma separated"
              value={tagsB}
              onChange={e => setTagsB(e.target.value)}
            />
          </div>
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          Create Test
        </button>
      </form>
      {testId && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Test ID: {testId}</h2>
          {metrics && (
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  <th className="px-2">Variant</th>
                  <th className="px-2">Impressions</th>
                  <th className="px-2">Clicks</th>
                  <th className="px-2">Conversion</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map(m => (
                  <tr key={m.variant_name} className="text-center">
                    <td className="border px-2 py-1">{m.variant_name}</td>
                    <td className="border px-2 py-1">{m.impressions}</td>
                    <td className="border px-2 py-1">{m.clicks}</td>
                    <td className="border px-2 py-1">
                      {(m.conversion_rate * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div className="space-x-2">
            <button
              onClick={() => clickVariant(variantA)}
              className="px-3 py-1 bg-green-600 text-white"
            >
              Click {variantA}
            </button>
            <button
              onClick={() => clickVariant(variantB)}
              className="px-3 py-1 bg-green-600 text-white"
            >
              Click {variantB}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

