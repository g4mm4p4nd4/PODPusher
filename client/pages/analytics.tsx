import React from 'react';
import { GetServerSideProps } from 'next';
import dynamic from 'next/dynamic';
import { useTranslation } from 'next-i18next';
import { useState } from 'react';
import { fetchSummary } from '../services/analytics';

const Bar = dynamic(() => import('react-chartjs-2').then((mod) => mod.Bar), { ssr: false });

export type SummaryRecord = {
  path: string;
  count: number;
};

interface AnalyticsProps {
  initialData: SummaryRecord[];
}

export default function Analytics({ initialData }: AnalyticsProps) {
  const { t } = useTranslation('common');
  const [eventType, setEventType] = useState('page_view');
  const [data, setData] = useState<SummaryRecord[]>(initialData);

  const fetchData = async (type: string) => {
    const res = await fetchSummary(type);
    setData(res);
  };

  const handleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const type = e.target.value;
    setEventType(type);
    await fetchData(type);
  };

  const chartData = {
    labels: data.map((d) => d.path),
    datasets: [
      {
        label: t('analytics.events'),
        data: data.map((d) => d.count),
        backgroundColor: 'rgba(99,102,241,0.5)',
      },
    ],
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('analytics.title')}</h1>
      <label htmlFor="eventType" className="block text-sm font-medium">
        {t('analytics.filter')}
      </label>
      <select
        id="eventType"
        value={eventType}
        onChange={handleChange}
        className="border p-2 rounded w-full md:w-60"
      >
        <option value="page_view">Page Views</option>
        <option value="click">Clicks</option>
        <option value="conversion">Conversions</option>
      </select>
      <Bar data={chartData} aria-label="analytics chart" role="img" />
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<AnalyticsProps> = async () => {
  try {
    const data = await fetchSummary('page_view');
    return { props: { initialData: data } };
  } catch (err) {
    console.error(err);
    return { props: { initialData: [] } };
  }
};
