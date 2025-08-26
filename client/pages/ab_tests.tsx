import { GetServerSideProps } from 'next';
import axios from 'axios';
import { useState } from 'react';
import { useTranslation } from 'next-i18next';

export type ABMetric = {
  id: number;
  test_id: number;
  name: string;
  weight: number;
  impressions: number;
  clicks: number;
  conversion_rate: number;
  experiment_type: string;
  start_time?: string | null;
  end_time?: string | null;
};

interface Props {
  metrics: ABMetric[];
}

export default function ABTests({ metrics: initial }: Props) {
  const { t } = useTranslation('common');
  const [metrics, setMetrics] = useState<ABMetric[]>(initial);
  const [name, setName] = useState('');
  const [variants, setVariants] = useState('');
  const [weights, setWeights] = useState('');
  const [experimentType, setExperimentType] = useState('image');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const parts = variants
      .split(',')
      .map(v => v.trim())
      .filter(Boolean);
    const weightParts = weights
      .split(',')
      .map(w => parseFloat(w.trim()))
      .filter(w => !isNaN(w));
    if (!name || !parts.length) return;
    try {
      const res = await axios.post(`${api}/ab_tests`, {
        name,
        experiment_type: experimentType,
        start_time: start ? new Date(start).toISOString() : null,
        end_time: end ? new Date(end).toISOString() : null,
        variants: parts.map((name, i) => ({ name, weight: weightParts[i] ?? 1 / parts.length })),
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
        <input
          className="border p-2"
          placeholder={t('ab.weights') as string}
          value={weights}
          onChange={e => setWeights(e.target.value)}
        />
        <select
          className="border p-2"
          value={experimentType}
          onChange={e => setExperimentType(e.target.value)}
        >
          <option value="image">{t('ab.types.image')}</option>
          <option value="description">{t('ab.types.description')}</option>
          <option value="price">{t('ab.types.price')}</option>
        </select>
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
              <td className="border px-2">{(m.weight * 100).toFixed(0)}%</td>
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
