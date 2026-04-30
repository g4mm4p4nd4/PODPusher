import { useRouter } from 'next/router';
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
import {
  DashboardResponse,
  addTagClusterToWatchlist,
  fetchTrendInsights,
  saveTrendKeyword,
  watchTrendKeyword,
} from '../services/controlCenter';
import {
  LiveTrendSignal,
  LiveTrendsMetaResponse,
  MarketExample,
  TrendRefreshStatus,
  fetchLiveTrendStatus,
  fetchLiveTrends,
  refreshLiveTrends,
} from '../services/trends';
import { getCommonStaticProps } from '../utils/translationProps';

export default function TrendsPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [marketplace, setMarketplace] = useState('etsy');
  const [category, setCategory] = useState('all');
  const [country, setCountry] = useState('US');
  const [language, setLanguage] = useState('en');
  const [dateRange, setDateRange] = useState('30');
  const [moreFiltersOpen, setMoreFiltersOpen] = useState(false);
  const [selectedKeyword, setSelectedKeyword] = useState<any>(null);
  const [actionStatus, setActionStatus] = useState('');
  const [loading, setLoading] = useState(true);
  const [liveData, setLiveData] = useState<LiveTrendsMetaResponse | null>(null);
  const [liveStatus, setLiveStatus] = useState<TrendRefreshStatus | null>(null);
  const [liveLoading, setLiveLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    const result = await fetchTrendInsights({
        marketplace,
        category: category === 'all' ? undefined : category,
        country,
        language,
        lookback_days: Number(dateRange),
    });
    setData(result);
    setSelectedKeyword((current: any) => current || (result.keywords || [])[0] || null);
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, [marketplace, category, country, language, dateRange]);

  const loadLiveRows = async () => {
    setLiveLoading(true);
    try {
      const result = await fetchLiveTrends({
        includeMeta: true,
        page: 1,
        pageSize: 10,
        limit: 10,
        sortBy: 'timestamp',
        sortOrder: 'desc',
      });
      setLiveData(result);
    } finally {
      setLiveLoading(false);
    }
  };

  const loadLiveStatus = async () => {
    const status = await fetchLiveTrendStatus();
    setLiveStatus(status);
  };

  const refreshLiveRows = async () => {
    setLiveLoading(true);
    try {
      const status = await refreshLiveTrends();
      setLiveStatus(status);
      const result = await fetchLiveTrends({
        includeMeta: true,
        page: 1,
        pageSize: 10,
        limit: 10,
        sortBy: 'timestamp',
        sortOrder: 'desc',
      });
      setLiveData(result);
    } finally {
      setLiveLoading(false);
    }
  };

  useEffect(() => {
    void loadLiveRows();
    void loadLiveStatus();
  }, []);

  const composerUrl = (payload: Record<string, string | undefined>) => {
    const params = new URLSearchParams();
    Object.entries(payload).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    return `/listing-composer?${params.toString()}`;
  };

  const useKeywordInComposer = (item: any) => {
    const example = firstMarketExample(item);
    void router.push(
      composerUrl({
        source: 'trends',
        keyword: item.keyword,
        niche: item.keyword,
        product_type: item.suggested_products?.[0],
        tags: (item.suggested_products || []).join(','),
        ...evidencePayload(example),
      })
    );
  };

  const useIdeaInComposer = (idea: any) => {
    const example = firstMarketExample(idea);
    void router.push(
      composerUrl({
        source: 'trend-design-idea',
        keyword: idea.keyword || idea.title,
        niche: idea.niche || idea.title,
        product_type: idea.product_type || 'T-Shirt',
        ...evidencePayload(example),
      })
    );
  };

  const saveKeyword = async (item: any) => {
    setActionStatus(`Saving ${item.keyword}...`);
    await saveTrendKeyword(item.keyword, item.search_volume || item.growth || 0);
    setActionStatus(`${item.keyword} saved to niches.`);
  };

  const watchKeyword = async (item: any) => {
    setActionStatus(`Watching ${item.keyword}...`);
    await watchTrendKeyword(item.keyword, item);
    setActionStatus(`${item.keyword} added to watchlist.`);
  };

  const addCluster = async (cluster: any) => {
    setActionStatus(`Adding ${cluster.cluster} cluster...`);
    await addTagClusterToWatchlist(cluster.cluster, cluster.tags || [], cluster.volume);
    setActionStatus(`${cluster.cluster} cluster added to watchlist.`);
  };

  const exportCsv = () => {
    const rows = data?.keywords || [];
    const header = ['rank', 'keyword', 'search_volume', 'growth', 'competition', 'opportunity'];
    const csv = [
      header.join(','),
      ...rows.map((row: any) =>
        header.map((key) => JSON.stringify(row[key] ?? '')).join(',')
      ),
    ].join('\n');

    if (typeof window === 'undefined' || typeof Blob === 'undefined' || !URL.createObjectURL) {
      setActionStatus('CSV export ready; browser download is unavailable in this environment.');
      return;
    }

    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `trend-keywords-${dateRange}d.csv`;
    link.click();
    URL.revokeObjectURL(url);
    setActionStatus(`Exported ${rows.length} keyword rows.`);
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Trend & Keyword Insights"
        subtitle="Discover what's trending, what's rising, and what to create next."
        actions={<Button onClick={load}>Refresh Insights</Button>}
      />
      <FilterBar>
        <SelectBox label="Marketplace" value={marketplace} onChange={setMarketplace} options={['etsy', 'Amazon US']} />
        <SelectBox label="Date Range" value={dateRange} onChange={setDateRange} options={['7', '30', '90', '180']} />
        <SelectBox label="Category" value={category} onChange={setCategory} options={['all', 'Apparel', 'Drinkware', 'Mugs', 'Bags']} />
        <SelectBox label="Country" value={country} onChange={setCountry} options={['US', 'CA', 'GB', 'DE', 'FR']} />
        <SelectBox label="Language" value={language} onChange={setLanguage} options={['en', 'es', 'fr', 'de']} />
        <Button onClick={() => setMoreFiltersOpen(!moreFiltersOpen)}>
          {moreFiltersOpen ? 'Hide Filters' : 'More Filters'}
        </Button>
      </FilterBar>
      {moreFiltersOpen ? (
        <Panel title="More Filters">
          <div className="grid gap-3 text-sm text-slate-400 md:grid-cols-3">
            <p>Source status: public trend signals and local estimator fallback.</p>
            <p>Credential-backed marketplaces are non-blocking in this slice.</p>
            <p>Selected keyword: {selectedKeyword?.keyword || 'None'}</p>
          </div>
        </Panel>
      ) : null}
      {actionStatus ? <EmptyState message={actionStatus} /> : null}

      <LiveScrapeRowsPanel
        data={liveData}
        status={liveStatus}
        loading={liveLoading}
        onRefresh={refreshLiveRows}
        onReload={loadLiveRows}
      />

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
            <Panel title="Trending Keywords" action={<Button onClick={exportCsv}>Export CSV</Button>}>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-left text-slate-500">
                    <tr>
                      <th className="py-2">#</th>
                      <th>Keyword</th>
                      <th>Market Evidence</th>
                      <th>Search Volume</th>
                      <th>Growth</th>
                      <th>Competition</th>
                      <th>Products</th>
                      <th>Opportunity</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data.keywords || []).map((item: any) => (
                      <tr
                        key={item.keyword}
                        className={`border-t border-slate-800 ${selectedKeyword?.keyword === item.keyword ? 'bg-orange-500/5' : ''}`}
                      >
                        <td className="py-3 text-slate-500">{item.rank}</td>
                        <td>
                          <button type="button" onClick={() => setSelectedKeyword(item)} className="font-medium text-slate-100 hover:text-orange-300">
                            {item.keyword}
                          </button>
                        </td>
                        <td className="min-w-[150px]">
                          <MarketExamplePreview
                            example={firstMarketExample(item)}
                            fallbackTitle={item.keyword}
                            compact
                          />
                        </td>
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
                        <td>
                          <div className="flex flex-wrap gap-1">
                            <button type="button" onClick={() => saveKeyword(item)} className="text-blue-300">Save</button>
                            <a href={composerUrl({
                              source: 'trends',
                              keyword: item.keyword,
                              niche: item.keyword,
                              product_type: item.suggested_products?.[0],
                              tags: (item.suggested_products || []).join(','),
                              ...evidencePayload(firstMarketExample(item)),
                            })} className="text-orange-300">Compose</a>
                            <button type="button" onClick={() => watchKeyword(item)} className="text-emerald-300">Watch</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {selectedKeyword ? (
                <div className="mt-4 rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                  <div className="grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
                    <div className="space-y-3">
                      <p className="font-medium text-slate-100">{selectedKeyword.keyword}</p>
                      <p className="text-slate-500">
                        {formatNumber(selectedKeyword.search_volume)} searches, {selectedKeyword.competition}/100 competition.
                      </p>
                      <MarketExamplePreview
                        example={firstMarketExample(selectedKeyword)}
                        fallbackTitle={selectedKeyword.keyword}
                      />
                    </div>
                    <div className="space-y-3">
                      <MarketStrategyNotes strategy={selectedKeyword.strategy} />
                      <a
                        href={composerUrl({
                          source: 'trends',
                          keyword: selectedKeyword.keyword,
                          niche: selectedKeyword.keyword,
                          product_type: selectedKeyword.suggested_products?.[0],
                          tags: (selectedKeyword.suggested_products || []).join(','),
                          ...evidencePayload(firstMarketExample(selectedKeyword)),
                        })}
                        className="inline-flex rounded-md border border-orange-500 bg-orange-500 px-3 py-2 text-sm font-medium text-white transition hover:bg-orange-400"
                      >
                        Use in Composer
                      </a>
                    </div>
                  </div>
                </div>
              ) : null}
            </Panel>

            <div className="space-y-4">
              <Panel title="Related Design Ideas">
                <div className="grid gap-3 sm:grid-cols-2">
                  {(data.design_ideas || []).map((idea: any) => (
                    <div key={idea.title} className="space-y-3 rounded-md border border-slate-800 bg-slate-950 p-3">
                      <div>
                        <p className="text-sm font-medium text-slate-100">{idea.title}</p>
                        <p className="text-xs text-slate-500">{idea.product_type || 'Design concept'} / {idea.keyword || idea.niche}</p>
                      </div>
                      <MarketExamplePreview
                        example={firstMarketExample(idea)}
                        fallbackTitle={idea.keyword || idea.title}
                      />
                      <MarketStrategyNotes strategy={idea.strategy} compact />
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <Pill tone={idea.opportunity === 'High' ? 'green' : 'orange'}>{idea.opportunity} opportunity</Pill>
                        <a href={composerUrl({
                          source: 'trend-design-idea',
                          keyword: idea.keyword || idea.title,
                          niche: idea.niche || idea.title,
                          product_type: idea.product_type || 'T-Shirt',
                          ...evidencePayload(firstMarketExample(idea)),
                        })} className="text-sm text-orange-300">
                          Use in Composer
                        </a>
                      </div>
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
                      <button type="button" onClick={() => addCluster(cluster)} className="mt-3 text-sm text-orange-300">
                        Add cluster
                      </button>
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

function LiveScrapeRowsPanel({
  data,
  status,
  loading,
  onRefresh,
  onReload,
}: {
  data: LiveTrendsMetaResponse | null;
  status: TrendRefreshStatus | null;
  loading: boolean;
  onRefresh: () => void;
  onReload: () => void;
}) {
  const rows = Object.entries(data?.items_by_category || {}).flatMap(([category, items]) =>
    items.map((item) => ({ ...item, category: item.category || category }))
  );
  const diagnostics = status?.source_diagnostics || {};
  const diagnosticEntries = Object.entries(diagnostics);
  const finishedAt = status?.last_finished_at ? new Date(status.last_finished_at).toLocaleString() : 'Not run yet';

  return (
    <Panel
      title="Live Scrape Rows"
      action={
        <div className="flex flex-wrap gap-2">
          <Button onClick={onReload} disabled={loading}>Reload Rows</Button>
          <Button onClick={onRefresh} loading={loading} variant="primary">Refresh Scrape</Button>
        </div>
      }
    >
      <div className="mb-3 grid gap-2 text-sm text-slate-300 md:grid-cols-4">
        <ScrapeStat label="Mode" value={status?.last_mode || 'pending'} />
        <ScrapeStat label="Persisted" value={String(status?.signals_persisted ?? data?.pagination?.total ?? 0)} />
        <ScrapeStat label="Succeeded" value={String(status?.sources_succeeded?.length ?? 0)} />
        <ScrapeStat label="Finished" value={finishedAt} />
      </div>
      {rows.length ? (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr>
                <th className="py-2">Keyword</th>
                <th>Source</th>
                <th>Method</th>
                <th>Evidence</th>
                <th>Category</th>
                <th>Score</th>
                <th>Confidence</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <LiveScrapeRow
                  key={`${row.source}-${row.keyword}-${row.timestamp}`}
                  row={row}
                  method={diagnostics[row.source]?.method || status?.source_methods?.[row.source] || row.source}
                />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState message={loading ? 'Refreshing live scrape rows...' : 'No persisted live scrape rows yet.'} />
      )}
      {diagnosticEntries.length ? (
        <div className="mt-3 grid gap-2 text-xs text-slate-400 md:grid-cols-2 xl:grid-cols-3">
          {diagnosticEntries.map(([source, diagnostic]) => (
            <div key={source} className="rounded-md border border-slate-800 bg-slate-950 p-2">
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="font-medium text-slate-200">{source}</span>
                <Pill tone={diagnostic.status === 'success' ? 'green' : 'orange'}>{diagnostic.method}</Pill>
              </div>
              <p>{diagnostic.status}: {diagnostic.persisted} persisted from {diagnostic.collected} collected</p>
              {diagnostic.reason ? <p className="mt-1 line-clamp-2 text-slate-500">{diagnostic.reason}</p> : null}
            </div>
          ))}
        </div>
      ) : null}
      {data?.provenance ? <ProvenanceNote provenance={data.provenance} /> : null}
    </Panel>
  );
}

function ScrapeStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950 p-2">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="truncate font-medium text-slate-100">{value}</p>
    </div>
  );
}

function LiveScrapeRow({ row, method }: { row: LiveTrendSignal; method: string }) {
  const confidence = row.provenance?.confidence;
  return (
    <tr className="border-t border-slate-800">
      <td className="py-3 font-medium text-slate-100">{row.keyword}</td>
      <td>{row.source}</td>
      <td>{method}</td>
      <td className="min-w-[130px]">
        <MarketExampleSummary example={firstMarketExample(row)} fallbackTitle={row.keyword} />
      </td>
      <td>{row.category}</td>
      <td>{formatNumber(row.engagement_score)}</td>
      <td>{typeof confidence === 'number' ? `${Math.round(confidence * 100)}%` : 'n/a'}</td>
      <td className="text-slate-400">{new Date(row.timestamp).toLocaleString()}</td>
    </tr>
  );
}

type MarketStrategy = {
  variation_prompts?: string[];
  anti_patterns?: string[];
  evidence_summary?: string;
};

function firstMarketExample(item: any): MarketExample | null {
  const examples = Array.isArray(item?.market_examples) ? item.market_examples : [];
  return examples[0] || null;
}

function evidencePayload(example: MarketExample | null): Record<string, string | undefined> {
  if (!example) return {};
  return {
    evidence_title: example.title,
    evidence_source: example.source,
    evidence_url: example.source_url || undefined,
    evidence_image_url: example.image_url || undefined,
    evidence_type: example.example_type || undefined,
  };
}

function MarketExamplePreview({
  example,
  fallbackTitle,
  compact = false,
}: {
  example: MarketExample | null;
  fallbackTitle: string;
  compact?: boolean;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const title = example?.title || fallbackTitle;
  const source = example?.source || 'keyword_evidence';
  const isEstimated = example?.provenance?.is_estimated || example?.example_type === 'keyword_evidence';
  const hasImage = Boolean(example?.image_url && !imageFailed);
  const label = isEstimated ? 'Keyword evidence' : `Source / ${source}`;
  const body = (
    <div className="min-w-0">
      <p className={`${compact ? 'text-xs' : 'text-sm'} line-clamp-2 font-medium text-slate-100`}>
        {title}
      </p>
      <p className="mt-1 truncate text-xs text-slate-500">{source}</p>
    </div>
  );

  return (
    <div className={`overflow-hidden rounded-md border border-slate-800 bg-slate-950 ${compact ? 'w-36' : ''}`}>
      {hasImage ? (
        <img
          src={example?.image_url || ''}
          alt={title}
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setImageFailed(true)}
          className={`${compact ? 'h-20' : 'h-32'} w-full bg-slate-900 object-cover`}
        />
      ) : (
        <div className={`${compact ? 'min-h-[80px]' : 'min-h-[112px]'} flex items-center bg-slate-900 p-3`}>
          {body}
        </div>
      )}
      <div className="space-y-2 border-t border-slate-800 p-2">
        {hasImage ? body : null}
        <div className="flex flex-wrap items-center gap-1">
          <Pill tone={isEstimated ? 'orange' : 'green'}>{label}</Pill>
          {example?.source_url ? (
            <a
              href={example.source_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-blue-300"
            >
              Open
            </a>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function MarketExampleSummary({
  example,
  fallbackTitle,
}: {
  example: MarketExample | null;
  fallbackTitle: string;
}) {
  const title = example?.title || fallbackTitle;
  const source = example?.source || 'keyword';
  return (
    <div className="max-w-[180px]">
      <p className="line-clamp-1 text-xs text-slate-200">{title}</p>
      <p className="truncate text-xs text-slate-500">{source}</p>
    </div>
  );
}

function MarketStrategyNotes({
  strategy,
  compact = false,
}: {
  strategy?: MarketStrategy;
  compact?: boolean;
}) {
  const variations = strategy?.variation_prompts || [];
  const antiPatterns = strategy?.anti_patterns || [];
  if (!strategy && !variations.length && !antiPatterns.length) return null;

  return (
    <div className="space-y-2 rounded-md border border-slate-800 bg-slate-900 p-3 text-xs text-slate-400">
      {strategy?.evidence_summary ? (
        <p className="text-slate-300">{strategy.evidence_summary}</p>
      ) : null}
      {variations.length ? (
        <div>
          <p className="font-medium uppercase text-slate-500">Variation logic</p>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {variations.slice(0, compact ? 1 : 2).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {antiPatterns.length && !compact ? (
        <div>
          <p className="font-medium uppercase text-slate-500">Avoid</p>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {antiPatterns.slice(0, 2).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function MomentumChart({ data }: { data: Array<Record<string, number | string>> }) {
  if (!data.length) return <EmptyState message="No momentum data yet." />;
  const series = [
    { key: 'etsy_search_volume', label: 'Etsy search', color: 'rgb(249 115 22)' },
    { key: 'google_trends', label: 'Google trends', color: 'rgb(34 197 94)' },
    { key: 'internal_trend_score', label: 'Internal score', color: 'rgb(59 130 246)' },
  ];
  const max = Math.max(
    ...series.flatMap((item) => data.map((row) => Number(row[item.key]) || 0)),
    1
  );
  const lineFor = (key: string) =>
    data
      .map((item, index) => {
        const x = 4 + (index / Math.max(1, data.length - 1)) * 92;
        const y = 92 - ((Number(item[key]) || 0) / max) * 76;
        return `${x},${y}`;
      })
      .join(' ');
  return (
    <div className="space-y-3">
      <svg className="h-48 w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        {[20, 40, 60, 80].map((line) => (
          <line key={line} x1="0" x2="100" y1={line} y2={line} stroke="rgba(148,163,184,0.16)" strokeWidth="0.35" />
        ))}
        {series.map((item) => (
          <polyline key={item.key} points={lineFor(item.key)} fill="none" stroke={item.color} strokeWidth="1.7" />
        ))}
      </svg>
      <div className="grid gap-2 text-xs text-slate-400 md:grid-cols-3">
        {series.map((item) => (
          <div key={item.key} className="flex items-center gap-2">
            <span className="h-2 w-6 rounded-full" style={{ backgroundColor: item.color }} />
            {item.label}
          </div>
        ))}
      </div>
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
