import { useRouter } from 'next/router';
import React, { useEffect, useState } from 'react';

import {
  Button,
  FilterBar,
  LoadingState,
  PageHeader,
  Panel,
  Pill,
  ProgressBar,
  ProvenanceNote,
  SelectBox,
  formatNumber,
} from '../components/ControlCenter';
import {
  DashboardResponse,
  fetchSeasonalEvents,
  saveSeasonalEvent,
} from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

export default function SeasonalEventsPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [selected, setSelected] = useState<any>(null);
  const [region, setRegion] = useState('US');
  const [language, setLanguage] = useState('en');
  const [marketplace, setMarketplace] = useState('etsy');
  const [category, setCategory] = useState('all');
  const [horizon, setHorizon] = useState('6');
  const [visibleMonth, setVisibleMonth] = useState(() => new Date());
  const [saveStatus, setSaveStatus] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const result = await fetchSeasonalEvents({
      region,
      language,
      marketplace,
      category,
      horizon_months: Number(horizon),
    });
    setData(result);
    const requested = router.query.event ? String(router.query.event) : '';
    setSelected(
      (result.events || []).find((event: any) => event.name === requested) ||
      (result.events || [])[0] ||
      null
    );
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, [region, language, marketplace, category, horizon, router.query.event]);

  const saveSelected = async () => {
    if (!selected) return;
    setSaveStatus(`Saving ${selected.name}...`);
    const result = await saveSeasonalEvent(selected.name);
    setSelected({ ...selected, saved: true });
    setSaveStatus(result.saved ? `${selected.name} saved to My Events.` : `${selected.name} save is unavailable.`);
  };

  const monthLabel = visibleMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const monthStart = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);
  const calendarStart = new Date(monthStart);
  calendarStart.setDate(monthStart.getDate() - monthStart.getDay());
  const calendarDays = Array.from({ length: 42 }, (_, index) => {
    const date = new Date(calendarStart);
    date.setDate(calendarStart.getDate() + index);
    return date;
  });

  const showToday = () => setVisibleMonth(new Date());

  const shiftMonth = (months: number) => {
    setVisibleMonth(new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + months, 1));
  };

  const selectedListings = selected
    ? (selected.product_categories || []).reduce((sum: number, item: any) => sum + Number(item.listings || 0), 0)
    : 0;

  const composerHref = selected
    ? `/listing-composer?source=seasonal&keyword=${encodeURIComponent(selected.recommended_keywords?.[0]?.keyword || selected.name)}&niche=${encodeURIComponent(selected.name)}&occasion=${encodeURIComponent(selected.name)}`
    : '/listing-composer';

  const eventForDate = (date: Date) =>
    (data?.events || []).find((item: any) => {
      const eventDate = new Date(`${item.event_date}T00:00:00`);
      return eventDate.toDateString() === date.toDateString();
    });

  const priorityTone = (priority: string) =>
    priority === 'high' ? 'red' : priority === 'medium' ? 'orange' : priority === 'awareness' ? 'blue' : 'green';

  const clearFilters = () => {
    setCategory('all');
    setHorizon('6');
    setRegion('US');
    setLanguage('en');
    setMarketplace('etsy');
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Seasonal Events Calendar"
        subtitle="Plan ahead. Discover opportunities. Launch with confidence."
        actions={<Button onClick={load}>Apply Filters</Button>}
      />
      <FilterBar>
        <SelectBox label="Region" value={region} onChange={setRegion} options={['US', 'North America', 'GB', 'DE']} />
        <SelectBox label="Language" value={language} onChange={setLanguage} options={['en', 'es', 'fr', 'de']} />
        <SelectBox label="Marketplace" value={marketplace} onChange={setMarketplace} options={['etsy', 'Amazon US']} />
        <SelectBox label="Category" value={category} onChange={setCategory} options={['all', 'Apparel', 'Drinkware', 'Mugs', 'Bags']} />
        <SelectBox label="Time Horizon" value={horizon} onChange={setHorizon} options={['3', '6', '12']} />
        <Button onClick={clearFilters}>Clear Filters</Button>
      </FilterBar>
      {saveStatus ? <div className="rounded-md border border-slate-800 bg-slate-900 p-3 text-sm text-slate-300">{saveStatus}</div> : null}

      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
            <Panel
              title={monthLabel}
              action={
                <div className="flex items-center gap-2">
                  <Button onClick={() => shiftMonth(-1)}>Prev</Button>
                  <Button onClick={() => shiftMonth(1)}>Next</Button>
                  <Button onClick={showToday}>Today</Button>
                </div>
              }
            >
              <div className="mb-4 grid gap-3 md:grid-cols-2">
                <div className="rounded-md border border-slate-800 bg-slate-950 p-4">
                  <p className="text-sm text-slate-400">Seasonal Opportunity Score</p>
                  <div className="mt-2 text-4xl font-semibold text-emerald-400">{data.opportunity_score}/100</div>
                  <ProgressBar value={data.opportunity_score} tone="green" />
                </div>
                <div className="rounded-md border border-slate-800 bg-slate-950 p-4">
                  <p className="text-sm text-slate-400">Listings to Prepare</p>
                  <div className="mt-2 text-4xl font-semibold text-slate-50">{data.listings_to_prepare}</div>
                  <p className="mt-2 text-sm text-slate-500">High-priority seasonal opportunities</p>
                </div>
              </div>
              <div className="mb-3 flex flex-wrap gap-2 text-xs">
                <Pill tone="red">High Priority</Pill>
                <Pill tone="orange">Medium</Pill>
                <Pill tone="green">Low</Pill>
                <Pill tone="blue">Awareness</Pill>
              </div>
              <div className="grid grid-cols-7 overflow-hidden rounded-md border border-slate-800 text-sm">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                  <div key={day} className="border-b border-slate-800 bg-slate-900 p-2 text-center text-slate-500">
                    {day}
                  </div>
                ))}
                {calendarDays.map((date) => {
                  const event = eventForDate(date);
                  const outsideMonth = date.getMonth() !== visibleMonth.getMonth();
                  return (
                    <button
                      key={date.toISOString()}
                      type="button"
                      onClick={() => event && setSelected(event)}
                      className={`min-h-[84px] border-b border-r border-slate-800 p-2 text-left hover:bg-slate-900 ${
                        selected?.name === event?.name ? 'bg-orange-500/10' : ''
                      }`}
                    >
                      <span className={outsideMonth ? 'text-slate-600' : 'text-slate-400'}>{date.getDate()}</span>
                      {event ? (
                        <div className={`mt-2 rounded px-2 py-1 text-xs ${
                          event.priority === 'high' ? 'bg-red-500/20 text-red-200' : 'bg-orange-500/20 text-orange-200'
                        }`}>
                          {event.name}
                        </div>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            </Panel>

            <div className="space-y-4">
              <Panel title="Upcoming High-Priority Events">
                <div className="space-y-2">
                  {(data.high_priority_events || []).map((event: any) => (
                    <button
                      key={event.name}
                      type="button"
                      onClick={() => setSelected(event)}
                      className={`w-full rounded-md border p-3 text-left text-sm ${
                        selected?.name === event.name ? 'border-orange-500 bg-orange-500/10' : 'border-slate-800 bg-slate-950'
                      }`}
                    >
                      <div className="flex justify-between">
                        <span className="font-medium text-slate-100">{event.name}</span>
                        <Pill tone={priorityTone(event.priority) as any}>{event.priority}</Pill>
                      </div>
                      <p className="text-xs text-slate-500">{event.event_date} - {event.days_away} days</p>
                    </button>
                  ))}
                </div>
              </Panel>

              {selected ? (
                <Panel
                  title={selected.name}
                  action={<Button onClick={saveSelected}>{selected.saved ? 'Saved' : 'Add to My Events'}</Button>}
                >
                  <p className="text-sm text-slate-400">
                    {selected.event_date} - {selected.days_away} days away
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Pill tone={priorityTone(selected.priority) as any}>{selected.priority} priority</Pill>
                    <Pill tone={selected.saved ? 'green' : 'slate'}>{selected.saved ? 'Saved' : 'Not saved'}</Pill>
                  </div>
                  <div className="mt-4 grid gap-3">
                    <div>
                      <p className="mb-2 text-sm font-medium">Recommended Keywords</p>
                      <div className="flex flex-wrap gap-2">
                        {selected.recommended_keywords.map((keyword: any) => (
                          <Pill key={keyword.keyword}>
                            {keyword.keyword} {formatNumber(keyword.volume)}
                          </Pill>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="mb-2 text-sm font-medium">Top Product Categories</p>
                      {selected.product_categories.slice(0, 4).map((item: any) => (
                        <div key={item.category} className="mb-2 flex justify-between text-sm">
                          <span>{item.category}</span>
                          <span className="text-slate-500">
                            Demand {item.demand}/100 - {formatNumber(item.listings)}
                          </span>
                        </div>
                      ))}
                    </div>
                    <div>
                      <p className="mb-2 text-sm font-medium">Niche Angles</p>
                      <div className="space-y-1 text-sm text-slate-400">
                        {selected.niche_angles.map((angle: string) => <p key={angle}>{angle}</p>)}
                      </div>
                    </div>
                    <div className="grid gap-3 md:grid-cols-2">
                      <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
                        <p className="text-sm font-medium">Ideal Launch Window</p>
                        <p className="mt-1 text-sm text-slate-400">Start 30-60 days before {selected.name}.</p>
                        <Pill tone="green">Launch 17-47 days before event</Pill>
                      </div>
                      <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
                        <p className="text-sm font-medium">Listing Count Opportunity</p>
                        <p className="mt-1 text-2xl font-semibold text-emerald-400">{formatNumber(Math.max(12000, selectedListings))}</p>
                        <p className="text-xs text-slate-500">Current comparable listings</p>
                      </div>
                    </div>
                    <a href={composerHref} className="rounded-md border border-orange-500 bg-orange-500 px-3 py-2 text-center text-sm font-medium text-white">
                      Use in Composer
                    </a>
                  </div>
                </Panel>
              ) : null}
            </div>
          </div>

          <Panel title="Create Early, Sell Early: Recommended Design Timeline">
            <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
              {(data.timeline || []).map((item: any) => (
                <div key={item.name} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                  <p className="font-medium text-slate-100">{item.name}</p>
                  <p className="mt-1 text-slate-500">Start by {item.start_by}</p>
                  <Pill tone={item.priority === 'high' ? 'red' : 'orange'}>{item.launch_window}</Pill>
                </div>
              ))}
            </div>
            <ProvenanceNote provenance={data.provenance} />
          </Panel>
        </>
      )}
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
