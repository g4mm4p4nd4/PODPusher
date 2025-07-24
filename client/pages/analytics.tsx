import { GetServerSideProps } from 'next';
import dynamic from 'next/dynamic';
import axios from 'axios';

const Chart = dynamic(() => import('react-chartjs-2').then(mod => mod.Bar), {
  ssr: false,
});

export type KeywordClicks = {
  keyword: string;
  clicks: number;
};

interface AnalyticsProps {
  data: KeywordClicks[];
}

export default function Analytics({ data }: AnalyticsProps) {
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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">Keyword Analytics</h1>
      <Chart data={chartData} />
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
