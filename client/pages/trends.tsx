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
import { DashboardResponse, fetchTrendInsights } from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

export default function TrendsPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [marketplace, setMarketplace] = useState('etsy');
  const [category, setCategory] = useState('all');
  const [country, setCountry] = useState('US');
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setData(
      await fetchTrendInsights({
        marketplace,
        category: category === 'all' ? undefined : category,
        country,
        language,
      })
    );
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="space-y-4">
      <PageHeader
        title="Trend & Keyword Insights"
        subtitle="Discover what's trending, what's rising, and what to create next."
        actions={<Button onClick={load}>Refresh Insights</Button>}
      />
      <FilterBar>
        <SelectBox label="Marketplace" value={marketplace} onChange={setMarketplace} options={['etsy', 'Amazon US']} />
        <SelectBox label="Category" value={category} onChange={setCategory} options={['all', 'Apparel', 'Drinkware', 'Mugs', 'Bags']} />
        <SelectBox label="Country" value={country} onChange={setCountry} options={['US', 'CA', 'GB', 'DE', 'FR']} />
        <SelectBox label="Language" value={language} onChange={setLanguage} options={['en', 'es', 'fr', 'de']} />
      </FilterBar>

      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <MetricGrid metrics={data.cards || []} />
          <div className="grid gap-4 xl:grid-cols-[1.45fr_0.8fr]">
            <Panel title="Keyword Momentum Over Time" action={<Pill>Last 30 Days</Pill>}>
              <MomentumChart data={data.momentum || []} />
            </Panel>
            <Panel title="Popular Product Categories">
              <div className="space-y-3">
                {(data.product_categories || []).map((item: any) => (
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
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.4fr_0.85fr]">
            <Panel title="Trending Keywords" action={<Button>Export CSV</Button>}>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-left text-slate-500">
                    <tr>
                      <th className="py-2">#</th>
                      <th>Keyword</th>
                      <th>Search Volume</th>
                      <th>Growth</th>
                      <th>Competition</th>
                      <th>Products</th>
                      <th>Opportunity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data.keywords || []).map((item: any) => (
                      <tr key={item.keyword} className="border-t border-slate-800">
                        <td className="py-3 text-slate-500">{item.rank}</td>
                        <td className="font-medium text-slate-100">{item.keyword}</td>
                        <td>{formatNumber(item.search_volume)}</td>
                        <td className="text-emerald-400">+{item.growth}%</td>
                        <td>{item.competition}/100</td>
                        <td className="space-x-1">
                          {(item.suggested_products || []).slice(0, 3).map((product: string) => (
                            <Pill key={product}>{product}</Pill>
                          ))}
                        </td>
                        <td>
                          <Pill tone={item.opportunity === 'High' ? 'green' : 'orange'}>{item.opportunity}</Pill>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>

            <div className="space-y-4">
              <Panel title="Related Design Ideas">
                <div className="grid gap-3 sm:grid-cols-2">
                  {(data.design_ideas || []).map((idea: any) => (
                    <div key={idea.title} className="rounded-md border border-slate-800 bg-slate-950 p-3">
                      <div className="mb-3 flex aspect-[4/3] items-center justify-center rounded bg-slate-800 text-center text-sm font-semibold text-orange-300">
                        {idea.title}
                      </div>
                      <Pill tone={idea.opportunity === 'High' ? 'green' : 'orange'}>{idea.opportunity} opportunity</Pill>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel title="Suggested Tag Clusters">
                <div className="space-y-3">
                  {(data.tag_clusters || []).map((cluster: any) => (
                    <div key={cluster.cluster} className="rounded-md border border-slate-800 bg-slate-950 p-3">
                      <div className="mb-2 flex justify-between text-sm">
                        <span className="font-medium">{cluster.cluster}</span>
                        <span className="text-slate-500">{formatNumber(cluster.volume)}</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {cluster.tags.map((tag: string) => <Pill key={tag}>{tag}</Pill>)}
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>
          </div>
          <ProvenanceNote provenance={data.provenance} />
        </>
      )}
    </div>
  );
}

function MomentumChart({ data }: { data: Array<Record<string, number | string>> }) {
  if (!data.length) return <EmptyState message="No momentum data yet." />;
  const series = ['etsy_search_volume', 'google_trends', 'internal_trend_score'];
  return (
    <div className="grid gap-3">
      {series.map((key) => {
        const max = Math.max(...data.map((item) => Number(item[key]) || 0), 1);
        return (
          <div key={key}>
            <div className="mb-1 text-xs text-slate-500">{key.replace(/_/g, ' ')}</div>
            <div className="flex h-10 items-end gap-1">
              {data.map((item, index) => (
                <span
                  key={`${key}-${index}`}
                  className="flex-1 rounded-t bg-orange-500/70"
                  style={{ height: `${Math.max(6, (Number(item[key]) / max) * 40)}px` }}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
