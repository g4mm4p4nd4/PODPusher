import { GetServerSideProps } from 'next';
import axios from 'axios';
import { useState } from 'react';
import dynamic from 'next/dynamic';
import { useTranslation } from 'next-i18next';
import 'chart.js/auto';

const Bar = dynamic(() => import('react-chartjs-2').then(mod => mod.Bar), {
  ssr: false,
});

export type ABMetric = {
  id: number;
  test_id: number;
  listing_id: number;
  title: string;
  description: string;
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
  const [variants, setVariants] = useState([
    { listingId: '', title: '', description: '' },
  ]);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const addVariant = () =>
    setVariants([...variants, { listingId: '', title: '', description: '' }]);

  const updateVariant = (
    idx: number,
    field: 'listingId' | 'title' | 'description',
    value: string,
  ) => {
    const copy = [...variants];
    (copy[idx] as any)[field] = value;
    setVariants(copy);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      name,
      variants: variants
        .filter(v => v.listingId && v.title && v.description)
        .map(v => ({
          listing_id: Number(v.listingId),
          title: v.title,
          description: v.description,
        })),
    };
    if (!payload.name || payload.variants.length === 0) return;
    try {
      const res = await axios.post(`${api}/api/ab-tests/`, payload);
      const metricsRes = await axios.get<ABMetric[]>(
        `${api}/api/ab-tests/${res.data.id}/metrics`,
      );
      setMetrics(metricsRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('ab.title')}</h1>
      <form onSubmit={submit} className="flex flex-col gap-4 max-w-md">
        <label className="flex flex-col">
          <span className="mb-1">{t('ab.name')}</span>
          <input
            className="border p-2"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </label>
        {variants.map((v, idx) => (
          <div key={idx} className="border p-2 space-y-2">
            <label className="flex flex-col">
              <span className="mb-1">{t('ab.listingId')}</span>
              <input
                className="border p-2"
                value={v.listingId}
                onChange={e => updateVariant(idx, 'listingId', e.target.value)}
              />
            </label>
            <label className="flex flex-col">
              <span className="mb-1">{t('ab.variantTitle')}</span>
              <input
                className="border p-2"
                value={v.title}
                onChange={e => updateVariant(idx, 'title', e.target.value)}
              />
            </label>
            <label className="flex flex-col">
              <span className="mb-1">{t('ab.variantDescription')}</span>
              <input
                className="border p-2"
                value={v.description}
                onChange={e => updateVariant(idx, 'description', e.target.value)}
              />
            </label>
          </div>
        ))}
        <button
          type="button"
          onClick={addVariant}
          className="bg-gray-200 px-4 py-2"
        >
          {t('ab.addVariant')}
        </button>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          {t('ab.create')}
        </button>
      </form>
      {metrics.length > 0 && (
        <div className="max-w-xl">
          <Bar
            data={{
              labels: metrics.map(m => m.title),
              datasets: [
                {
                  label: t('ab.rate'),
                  data: metrics.map(m => m.conversion_rate * 100),
                  backgroundColor: 'rgba(59,130,246,0.5)',
                },
              ],
            }}
            aria-label={t('ab.chart') as string}
          />
        </div>
      )}
      <table className="min-w-full border">
        <thead>
          <tr>
            <th className="border px-2">{t('ab.variant')}</th>
            <th className="border px-2">{t('ab.impressions')}</th>
            <th className="border px-2">{t('ab.clicks')}</th>
            <th className="border px-2">{t('ab.rate')}</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map(m => (
            <tr key={m.id}>
              <td className="border px-2">{m.title}</td>
              <td className="border px-2" data-testid={`imp-${m.id}`}>
                {m.impressions}
              </td>
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
    const res = await axios.get<ABMetric[]>(`${api}/api/ab-tests/metrics`);
    return { props: { metrics: res.data } };
  } catch (err) {
    console.error(err);
    return { props: { metrics: [] } };
  }
};

