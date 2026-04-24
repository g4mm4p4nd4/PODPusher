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
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [selected, setSelected] = useState<any>(null);
  const [region, setRegion] = useState('US');
  const [language, setLanguage] = useState('en');
  const [marketplace, setMarketplace] = useState('etsy');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const result = await fetchSeasonalEvents({ region, language, marketplace, horizon_months: 6 });
    setData(result);
    setSelected((result.events || [])[0] || null);
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, []);

  const saveSelected = async () => {
    if (!selected) return;
    await saveSeasonalEvent(selected.name);
    await load();
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
      </FilterBar>

      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
            <Panel title="Calendar">
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
              <div className="grid grid-cols-7 overflow-hidden rounded-md border border-slate-800 text-sm">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                  <div key={day} className="border-b border-slate-800 bg-slate-900 p-2 text-center text-slate-500">
                    {day}
                  </div>
                ))}
                {Array.from({ length: 35 }).map((_, index) => {
                  const event = (data.events || []).find((item: any) => Number(item.event_date.slice(-2)) === index + 1);
                  return (
                    <button
                      key={index}
                      type="button"
                      onClick={() => event && setSelected(event)}
                      className="min-h-[84px] border-b border-r border-slate-800 p-2 text-left hover:bg-slate-900"
                    >
                      <span className="text-slate-500">{index + 1}</span>
                      {event ? (
                        <div className="mt-2 rounded bg-orange-500/20 px-2 py-1 text-xs text-orange-200">
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
                        <Pill tone="red">High</Pill>
                      </div>
                      <p className="text-xs text-slate-500">{event.event_date} - {event.days_away} days</p>
                    </button>
                  ))}
                </div>
              </Panel>

              {selected ? (
                <Panel title={selected.name} action={<Button onClick={saveSelected}>Add to My Events</Button>}>
                  <p className="text-sm text-slate-400">
                    {selected.event_date} - {selected.days_away} days away
                  </p>
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
                          <span className="text-slate-500">{formatNumber(item.listings)}</span>
                        </div>
                      ))}
                    </div>
                    <div>
                      <p className="mb-2 text-sm font-medium">Niche Angles</p>
                      <div className="space-y-1 text-sm text-slate-400">
                        {selected.niche_angles.map((angle: string) => <p key={angle}>{angle}</p>)}
                      </div>
                    </div>
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
