import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { useTranslation } from 'next-i18next';
import AnalyticsChart from '../components/AnalyticsChart';
import { fetchTrendingKeywords, TrendingKeyword } from '../services/analytics';

export default function Analytics() {
  const { t, i18n } = useTranslation('common');
  const [keywords, setKeywords] = useState<TrendingKeyword[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const emptyMessage = t('analytics.empty');
  const errorMessage = t('analytics.error');

  useEffect(() => {
    let isActive = true;

    const loadAnalytics = async () => {
      try {
        const data = await fetchTrendingKeywords();
        if (!isActive) {
          return;
        }
        if (!Array.isArray(data) || data.length === 0) {
          setError(emptyMessage);
          setKeywords([]);
          return;
        }
        const sorted = [...data].sort((a, b) => b.clicks - a.clicks);
        setKeywords(sorted);
        setError(null);
      } catch (err) {
        if (isActive) {
          setError(errorMessage);
          setKeywords([]);
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    };

    loadAnalytics();

    return () => {
      isActive = false;
    };
  }, [emptyMessage, errorMessage, i18n?.language]);

  return (
    <div className="space-y-6">
      <Head>
        <title>{t('analytics.title')}</title>
      </Head>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{t('analytics.title')}</h1>
      {loading && <p className="text-gray-600 dark:text-gray-300">{t('analytics.loading')}</p>}
      {error ? (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
        >
          {error}
        </div>
      ) : (
        <AnalyticsChart
          keywords={keywords}
          title={t('analytics.trendingKeywords')}
          termLabel={t('analytics.term')}
          clicksLabel={t('analytics.clicks')}
          tableLabel={t('analytics.tableLabel')}
        />
      )}
    </div>
  );
}
