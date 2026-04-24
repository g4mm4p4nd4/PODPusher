import React, { useEffect, useState } from 'react';

import {
  Button,
  EmptyState,
  LoadingState,
  MetricGrid,
  PageHeader,
  Panel,
  Pill,
  ProgressBar,
  ProvenanceNote,
  formatNumber,
} from '../components/ControlCenter';
import { DashboardResponse, fetchOverview } from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

export default function Home() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      setData(await fetchOverview());
      setError('');
    } catch {
      setError('Could not load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState message={error || 'No overview data available.'} />;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Overview Dashboard"
        subtitle="Your POD business at a glance. Key metrics, trends, and opportunities."
        actions={<Button onClick={load}>Refresh</Button>}
      />
      <MetricGrid metrics={data.metrics || []} />

      <div className="grid gap-4 xl:grid-cols-[1.35fr_1fr]">
        <Panel title="Keyword Growth Trend" action={<Pill>Last 30 Days</Pill>}>
          <div className="h-64">
            <TrendArea data={data.keyword_growth || []} />
          </div>
        </Panel>
        <Panel title="Top Rising Niches" action={<a className="text-sm text-blue-400" href="/niches">View all</a>}>
          <div className="space-y-3">
            {(data.top_rising_niches || []).map((item: any) => (
              <div key={item.niche} className="grid grid-cols-[1fr_80px_110px] items-center gap-3 text-sm">
                <span className="font-medium text-slate-100">{item.niche}</span>
                <span className="text-emerald-400">+{item.growth}%</span>
                <span className="text-slate-400">{item.competition_label}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-4">
        <Panel title="Popular Product Categories">
          <div className="space-y-3">
            {(data.popular_categories || []).slice(0, 5).map((item: any) => (
              <div key={item.category}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{item.category}</span>
                  <span className="text-slate-400">{formatNumber(item.listings)}</span>
                </div>
                <ProgressBar value={item.demand} />
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Upcoming Seasonal Events">
          <div className="space-y-3">
            {(data.seasonal_events || []).slice(0, 5).map((event: any) => (
              <div key={event.name} className="flex items-center justify-between gap-2 text-sm">
                <div>
                  <p className="font-medium text-slate-100">{event.name}</p>
                  <p className="text-xs text-slate-500">{event.event_date}</p>
                </div>
                <Pill tone={event.priority === 'high' ? 'red' : 'orange'}>{event.priority}</Pill>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Recent Listing Composer">
          <div className="space-y-3">
            {(data.recent_drafts || []).map((draft: any) => (
              <div key={`${draft.id}-${draft.title}`} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                <p className="font-medium text-slate-100">{draft.title}</p>
                <p className="text-xs text-slate-500">{draft.language} draft</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="A/B Test Performance">
          <div className="space-y-3">
            {(data.ab_performance || []).map((test: any) => (
              <div key={test.test} className="grid grid-cols-[1fr_70px_70px] gap-2 text-sm">
                <span>{test.test}</span>
                <span>{test.ctr}%</span>
                <span className={test.lift >= 0 ? 'text-emerald-400' : 'text-red-400'}>{test.lift} pp</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Notifications" action={<a className="text-sm text-blue-400" href="/notifications">View all</a>}>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {(data.notifications || []).map((item: any) => (
            <div key={`${item.id}-${item.message}`} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
              <Pill tone={item.type === 'warning' ? 'orange' : item.type === 'success' ? 'green' : 'blue'}>
                {item.type}
              </Pill>
              <p className="mt-2 text-slate-200">{item.message}</p>
            </div>
          ))}
        </div>
        <ProvenanceNote provenance={data.provenance} />
      </Panel>
    </div>
  );
}

function TrendArea({ data }: { data: Array<{ date: string; value: number }> }) {
  if (!data.length) return <EmptyState message="No growth data yet." />;
  const max = Math.max(...data.map((item) => item.value), 1);
  const points = data
    .map((item, index) => {
      const x = (index / Math.max(1, data.length - 1)) * 100;
      const y = 100 - (item.value / max) * 88;
      return `${x},${y}`;
    })
    .join(' ');
  return (
    <svg className="h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke="rgb(249 115 22)" strokeWidth="1.6" />
      <polygon points={`0,100 ${points} 100,100`} fill="rgba(249,115,22,0.18)" />
    </svg>
  );
}

export const getStaticProps = getCommonStaticProps;
