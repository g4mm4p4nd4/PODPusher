import React, { useEffect, useState } from 'react';
import { GetServerSideProps } from 'next';
import dynamic from 'next/dynamic';
import { useTranslation } from 'next-i18next';
import { fetchSummary } from '../services/analytics';
import { formatCurrency } from '../utils/format';

const Bar = dynamic(() => import('react-chartjs-2').then((mod) => mod.Bar), { ssr: false });

export type SummaryRecord = {
  path: string;
  views: number;
  clicks: number;
  conversions: number;
  conversion_rate: number;
  revenue?: number;
};

interface AnalyticsProps {
  initialData: SummaryRecord[];
}

export default function Analytics({ initialData }: AnalyticsProps) {
  const { t, i18n } = useTranslation('common');
  const [data, setData] = useState<SummaryRecord[]>(initialData);

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetchSummary();
      setData(res);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const listingData = data.filter((d) => d.path.startsWith('/listing'));

  const listingChart = {
    labels: listingData.map((d) => d.path),
    datasets: [
      {
        label: t('analytics.views'),
        data: listingData.map((d) => d.views),
        backgroundColor: 'rgba(99,102,241,0.5)',
      },
    ],
  };

  const conversionChart = {
    labels: data.map((d) => d.path),
    datasets: [
      {
        label: t('analytics.conversionRate'),
        data: data.map((d) => d.conversion_rate),
        backgroundColor: 'rgba(16,185,129,0.5)',
      },
    ],
  };

  const trafficChart = {
    labels: data.map((d) => d.path),
    datasets: [
      {
        label: t('analytics.views'),
        data: data.map((d) => d.views),
        backgroundColor: 'rgba(239,68,68,0.5)',
      },
    ],
  };

  const totalRevenue = data.reduce((sum, d) => sum + (d.revenue || 0), 0);
  const currency = 'USD';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('analytics.title')}</h1>
      <Bar data={listingChart} aria-label="listing views chart" role="img" />
      <Bar data={conversionChart} aria-label="conversion rate chart" role="img" />
      <Bar data={trafficChart} aria-label="traffic chart" role="img" />
      <p>
        {t('analytics.revenue')}: {formatCurrency(totalRevenue, currency, i18n.language)}
      </p>
    </div>
  );
}

export const getServerSideProps: GetServerSideProps<AnalyticsProps> = async () => {
  try {
    const data = await fetchSummary();
    return { props: { initialData: data } };
  } catch (err) {
    console.error(err);
    return { props: { initialData: [] } };
  }
};
