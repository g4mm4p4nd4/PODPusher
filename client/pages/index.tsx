import React from 'react';
import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { getCommonStaticProps } from '../utils/translationProps';

import { resolveApiUrl } from '../services/apiBase';
import {
  fetchLiveTrends,
  LiveTrendsByCategory,
  refreshLiveTrends,
  TrendRefreshStatus,
} from '../services/trends';

const EMPTY_STATUS: TrendRefreshStatus = {
  last_started_at: null,
  last_finished_at: null,
  last_mode: 'idle',
  sources_succeeded: [],
  sources_failed: {},
  signals_collected: 0,
  signals_persisted: 0,
};

export default function Home() {
  const { t } = useTranslation('common');
  const [trends, setTrends] = useState<LiveTrendsByCategory>({});
  const [events, setEvents] = useState<string[]>([]);
  const [status, setStatus] = useState<TrendRefreshStatus>(EMPTY_STATUS);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const hasTrends = Object.values(trends).some(items => items.length > 0);

  const loadDashboard = async () => {
    try {
      const month = new Date().toLocaleString('default', { month: 'long' }).toLowerCase();
      const [liveTrends, statusRes, eventsRes] = await Promise.all([
        fetchLiveTrends({ lookbackHours: 72, limit: 8 }),
        axios.get<TrendRefreshStatus>(resolveApiUrl('/api/trends/live/status')),
        axios.get<{ month: string; events: string[] }>(resolveApiUrl(`/events/${month}`)),
      ]);
      setTrends(liveTrends);
      setStatus(statusRes.data || EMPTY_STATUS);
      setEvents(Array.isArray(eventsRes.data.events) ? eventsRes.data.events : []);
      setError('');
    } catch (err) {
      console.error(err);
      setTrends({});
      setEvents([]);
      setError(t('index.loadError'));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void loadDashboard();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError('');
    try {
      const refreshStatus = await refreshLiveTrends();
      setStatus(refreshStatus);
    } catch (err) {
      console.error(err);
      setError(t('index.refreshError'));
      setRefreshing(false);
      return;
    }
    await loadDashboard();
  };

  const formatTimestamp = (value?: string | null): string => {
    if (!value) {
      return t('index.notAvailable');
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return t('index.notAvailable');
    }
    return parsed.toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">{t('index.trending')}</h1>
        <button
          type="button"
          onClick={handleRefresh}
          className="rounded bg-gray-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
          disabled={refreshing}
        >
          {refreshing ? t('index.refreshing') : t('index.refresh')}
        </button>
      </div>

      <div className="rounded border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
        <p>
          <span className="font-semibold">{t('index.lastRun')}:</span> {formatTimestamp(status.last_finished_at)}
        </p>
        <p>
          <span className="font-semibold">{t('index.mode')}:</span> {status.last_mode || t('index.notAvailable')}
        </p>
        <p>
          <span className="font-semibold">{t('index.signals')}:</span> {status.signals_persisted}
        </p>
      </div>

      {loading ? <p>{t('index.loading')}</p> : null}
      {error ? (
        <p role="alert" className="rounded border border-red-200 bg-red-50 p-3 text-red-700">
          {error}
        </p>
      ) : null}
      {!loading && !error && !hasTrends ? <p>{t('index.empty')}</p> : null}

      {Object.entries(trends).map(([category, items]) => (
        <section key={category}>
          <h2 className="text-xl font-semibold capitalize">{category}</h2>
          <ul className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2 lg:grid-cols-3">
            {items.map(item => (
              <li key={`${category}:${item.source}:${item.keyword}`} className="rounded border border-gray-200 p-3">
                <p className="font-medium">{item.keyword}</p>
                <p className="text-sm text-gray-600">
                  {t('index.source')}: {item.source}
                </p>
                <p className="text-sm text-gray-600">
                  {t('index.engagement')}: {item.engagement_score}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ))}

      <div>
        <h2 className="mt-4 text-xl font-semibold">{t('index.events')}</h2>
        <ul className="grid grid-cols-2 gap-1 list-disc list-inside pl-4 md:grid-cols-3 lg:grid-cols-4">
          {events.map(event => (
            <li key={event}>{event}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
