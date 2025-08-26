import { GetServerSideProps } from 'next';
import axios from 'axios';
import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';

export type ABMetric = {
  id: number;
  test_id: number;
  name: string;
  traffic_weight: number;
  impressions: number;
  clicks: number;
  conversion_rate: number;
};

interface Props {
  metrics: ABMetric[];
}

export default function ABTests({ metrics: initial }: Props) {
  const { t } = useTranslation('common');
  const [metrics, setMetrics] = useState<ABMetric[]>(initial);
  const [name, setName] = useState('');
  const [variants, setVariants] = useState('');
  const [expType, setExpType] = useState('image');
  const [weights, setWeights] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parts = variants
      .split(',')
      .map(v => v.trim())
      .filter(Boolean);
    if (!name || !parts.length) return;
    const split = weights
      .split(',')
      .map(w => parseFloat(w.trim()))
      .filter(w => !isNaN(w));
    try {
      const res = await axios.post(`${api}/ab_tests`, {
        name,
        variants: parts,
        experiment_type: expType,
        traffic_split: split.length === parts.length ? split : undefined,
        start_time: start || undefined,
        end_time: end || undefined,
      });
      const metricsRes = await axios.get<ABMetric[]>(
        `${api}/ab_tests/${res.data.id}/metrics`
      );
      setMetrics(metricsRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('ab.title')}</h1>
      <form onSubmit={submit} className="flex flex-col gap-2 max-w-md">
        <input
          className="border p-2"
          placeholder={t('ab.name') as string}
          value={name}
          onChange={e => setName(e.target.value)}
        />
        <input
          className="border p-2"
          placeholder={t('ab.variants') as string}
          value={variants}
          onChange={e => setVariants(e.target.value)}
        />
        <select
          className="border p-2"
          value={expType}
          onChange={e => setExpType(e.target.value)}
        >
          <option value="image">Image</option>
          <option value="description">Description</option>
          <option value="pricing">Pricing</option>
        </select>
        <input
          className="border p-2"
          placeholder={t('ab.weights') as string}
          value={weights}
          onChange={e => setWeights(e.target.value)}
        />
        <input
          type="datetime-local"
          className="border p-2"
          placeholder={t('ab.start') as string}
          value={start}
          onChange={e => setStart(e.target.value)}
        />
        <input
          type="datetime-local"
          className="border p-2"
          placeholder={t('ab.end') as string}
          value={end}
          onChange={e => setEnd(e.target.value)}
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          {t('ab.create')}
        </button>
      </form>
      <table className="min-w-full border">
        <thead>
          <tr>
            <th className="border px-2">{t('ab.variant')}</th>
            <th className="border px-2">{t('ab.weight')}</th>
            <th className="border px-2">{t('ab.impressions')}</th>
            <th className="border px-2">{t('ab.clicks')}</th>
            <th className="border px-2">{t('ab.rate')}</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map(m => (
            <tr key={m.id}>
              <td className="border px-2">{m.name}</td>
              <td className="border px-2">{(m.traffic_weight * 100).toFixed(0)}%</td>
              <td className="border px-2" data-testid={`imp-${m.id}`}>{m.impressions}</td>
              <td className="border px-2">{m.clicks}</td>
              <td className="border px-2">{(m.conversion_rate * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<Props> = async () => {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  try {
    const res = await axios.get<ABMetric[]>(`${api}/ab_tests/metrics`);
    return { props: { metrics: res.data } };
  } catch (err) {
    console.error(err);
    return { props: { metrics: [] } };
  }
};

