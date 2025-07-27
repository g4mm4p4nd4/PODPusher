import { GetServerSideProps } from 'next';
import dynamic from 'next/dynamic';
import axios from 'axios';
import { useTranslation } from 'next-i18next';

const Chart = dynamic(() => import('react-chartjs-2').then(mod => mod.Bar), {
  ssr: false,
});

export type KeywordClicks = {
  keyword: string;
  clicks: number;
  revenue: number;
};

interface AnalyticsProps {
  data: KeywordClicks[];
}

export default function Analytics({ data }: AnalyticsProps) {
  const { t, i18n } = useTranslation('common');
  const chartData = {
    labels: data.map(d => d.keyword),
    datasets: [
      {
        label: 'Clicks',
        data: data.map(d => d.clicks),
        backgroundColor: 'rgba(99, 102, 241, 0.5)',
      },
    ],
  };

  const nf = new Intl.NumberFormat(i18n.language === 'es' ? 'es-ES' : 'en-US', {
    style: 'currency',
    currency: i18n.language === 'es' ? 'EUR' : 'USD',
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('analytics.title')}</h1>
      <Chart data={chartData} />
      <ul className="list-disc list-inside">
        {data.map(d => (
          <li key={d.keyword}>
            {d.keyword}: {nf.format(d.revenue)}
          </li>
        ))}
      </ul>
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<AnalyticsProps> = async () => {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  try {
    const res = await axios.get<KeywordClicks[]>(`${api}/analytics`);
    return { props: { data: res.data } };
  } catch (err) {
    console.error(err);
    return { props: { data: [] } };
  }
};
