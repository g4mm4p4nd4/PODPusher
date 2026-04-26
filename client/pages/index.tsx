import React, { useEffect, useState } from 'react';

import {
  Button,
  EmptyState,
  FilterBar,
  LoadingState,
  MetricGrid,
  PageHeader,
  Panel,
  Pill,
  ProgressBar,
  ProvenanceNote,
  SelectBox,
  formatNumber,
} from '../components/ControlCenter';
import { DashboardResponse, fetchOverviewDashboard } from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

export default function Home() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [dateRange, setDateRange] = useState('7');
  const [selectedEvent, setSelectedEvent] = useState<any>(null);
  const [selectedCategory, setSelectedCategory] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const dateTo = new Date();
      const dateFrom = new Date(dateTo);
      dateFrom.setDate(dateTo.getDate() - Number(dateRange));
      const result = await fetchOverviewDashboard({
        date_from: formatDateParam(dateFrom),
        date_to: formatDateParam(dateTo),
      });
      setData(result);
      setSelectedEvent((current: any) => current || (result.seasonal_events || [])[0] || null);
      setSelectedCategory((current: any) => current || (result.popular_categories || [])[0] || null);
      setError('');
    } catch {
      setError('Could not load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [dateRange]);

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState message={error || 'No overview data available.'} />;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Overview Dashboard"
        subtitle="Your POD business at a glance. Key metrics, trends, and opportunities."
        actions={<Button onClick={load}>Refresh</Button>}
      />
      <FilterBar>
        <SelectBox
          label="Date Range"
          value={dateRange}
          onChange={setDateRange}
          options={['7', '30', '90']}
        />
      </FilterBar>
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
              <a
                key={item.niche}
                href={`/niches?niche=${encodeURIComponent(item.niche)}`}
                className="grid grid-cols-[1fr_80px_110px] items-center gap-3 rounded-md px-2 py-1 text-sm hover:bg-slate-800"
              >
                <span className="font-medium text-slate-100">{item.niche}</span>
                <span className="text-emerald-400">+{item.growth}%</span>
                <span className="text-slate-400">{item.competition_label}</span>
              </a>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-4">
        <Panel title="Popular Product Categories">
          <div className="space-y-3">
            {(data.popular_categories || []).slice(0, 5).map((item: any) => (
              <button
                key={item.category}
                type="button"
                onClick={() => setSelectedCategory(item)}
                className={`block w-full rounded-md p-2 text-left ${
                  selectedCategory?.category === item.category ? 'bg-orange-500/10' : 'hover:bg-slate-800'
                }`}
              >
                <div className="mb-1 flex justify-between text-sm">
                  <span>{item.category}</span>
                  <span className="text-slate-400">{formatNumber(item.listings)}</span>
                </div>
                <ProgressBar value={item.demand} />
              </button>
            ))}
          </div>
          {selectedCategory ? (
            <div className="mt-3 rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
              <p className="font-medium text-slate-100">{selectedCategory.category}</p>
              <p className="text-slate-500">
                Demand {selectedCategory.demand}/100 with {formatNumber(selectedCategory.listings)} active listings.
              </p>
              <a className="mt-2 inline-block text-orange-300" href={`/search?category=${encodeURIComponent(selectedCategory.category)}`}>
                Drill into category
              </a>
            </div>
          ) : null}
        </Panel>

        <Panel title="Upcoming Seasonal Events">
          <div className="space-y-3">
            {(data.seasonal_events || []).slice(0, 5).map((event: any) => (
              <button
                key={event.name}
                type="button"
                onClick={() => setSelectedEvent(event)}
                className={`flex w-full items-center justify-between gap-2 rounded-md p-2 text-left text-sm ${
                  selectedEvent?.name === event.name ? 'bg-orange-500/10' : 'hover:bg-slate-800'
                }`}
              >
                <div>
                  <p className="font-medium text-slate-100">{event.name}</p>
                  <p className="text-xs text-slate-500">{event.event_date}</p>
                </div>
                <Pill tone={event.priority === 'high' ? 'red' : 'orange'}>{event.priority}</Pill>
              </button>
            ))}
          </div>
          {selectedEvent ? (
            <div className="mt-3 rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
              <p className="font-medium text-slate-100">{selectedEvent.name}</p>
              <p className="text-slate-500">{selectedEvent.days_away} days away</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {(selectedEvent.recommended_keywords || []).slice(0, 3).map((keyword: any) => (
                  <Pill key={keyword.keyword}>{keyword.keyword}</Pill>
                ))}
              </div>
              <a className="mt-2 inline-block text-orange-300" href={`/seasonal-events?event=${encodeURIComponent(selectedEvent.name)}`}>
                Open event detail
              </a>
            </div>
          ) : null}
        </Panel>

        <Panel title="Recent Listing Composer">
          <div className="space-y-3">
            {(data.recent_drafts || []).map((draft: any) => (
              <a
                key={`${draft.id}-${draft.title}`}
                href={draft.id ? `/listing-composer?draft=${draft.id}` : `/listing-composer?keyword=${encodeURIComponent(draft.title)}`}
                className="block rounded-md border border-slate-800 bg-slate-950 p-3 text-sm hover:border-orange-500/50"
              >
                <p className="font-medium text-slate-100">{draft.title}</p>
                <p className="text-xs text-slate-500">{draft.language} draft</p>
              </a>
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

function formatDateParam(date: Date) {
  return date.toISOString().slice(0, 10);
}

export const getStaticProps = getCommonStaticProps;
