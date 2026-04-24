import { useRouter } from 'next/router';
import React, { useEffect, useState } from 'react';

import {
  Button,
  FilterBar,
  LoadingState,
  PageHeader,
  Panel,
  Pill,
  SelectBox,
  TextInput,
  formatNumber,
} from '../components/ControlCenter';
import {
  DashboardResponse,
  addToWatchlist,
  fetchSearchInsights,
  saveSearch,
} from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [marketplace, setMarketplace] = useState('etsy');
  const [season, setSeason] = useState('Summer');
  const [niche, setNiche] = useState('all');
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const results = (data?.results || data?.items || []) as any[];

  const runSearch = async () => {
    setLoading(true);
    const raw = await fetchSearchInsights({
      q: query,
      category: category === 'all' ? undefined : category,
      marketplace,
      season,
      niche: niche === 'all' ? undefined : niche,
    });
    setData(raw);
    setLoading(false);
  };

  useEffect(() => {
    if (router.query.q) {
      setQuery(String(router.query.q));
    }
  }, [router.query.q]);

  useEffect(() => {
    void runSearch();
  }, []);

  const saveCurrentSearch = async () => {
    await saveSearch({
      name: query || 'Current Search',
      query,
      filters: { category, marketplace, season, niche },
      result_count: results.length,
    });
    await runSearch();
  };

  const watch = async (item: any) => {
    await addToWatchlist({ item_type: 'product', name: item.name, context: item });
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Search & Suggestions" actions={<Button onClick={saveCurrentSearch}>Save Search</Button>} />
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void runSearch();
        }}
      >
        <FilterBar>
          <TextInput label="Keyword" value={query} onChange={setQuery} placeholder="Keyword" />
          <SelectBox label="Category" value={category} onChange={setCategory} options={['all', 'Apparel', 'Drinkware', 'Mugs', 'Bags']} />
          <SelectBox label="Marketplace" value={marketplace} onChange={setMarketplace} options={['etsy', 'Amazon US']} />
          <SelectBox label="Season" value={season} onChange={setSeason} options={['Summer', 'Fall', 'Winter', 'Spring']} />
          <SelectBox label="Niche" value={niche} onChange={setNiche} options={['all', 'Dog Lovers', 'Pickleball', 'Teachers', 'Mental Health']} />
          <Button type="submit" variant="primary">Search</Button>
        </FilterBar>
      </form>

      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <div className="grid gap-4 xl:grid-cols-[1.35fr_0.75fr]">
            <Panel title={`Search Results (${formatNumber(data.total || results.length)} results)`}>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-left text-slate-500">
                    <tr>
                      <th className="py-2">Product</th>
                      <th>Category</th>
                      <th>Rating</th>
                      <th>Trend Score</th>
                      <th>Demand Signal</th>
                      <th>Quick Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((item) => (
                      <tr key={item.id || item.name} className="border-t border-slate-800">
                        <td className="py-3 font-medium text-slate-100">{item.name}</td>
                        <td>{item.category}</td>
                        <td>{item.rating ? `${item.rating} stars` : 'Unrated'}</td>
                        <td className="text-emerald-400">{item.trend_score || 72}</td>
                        <td>
                          <Pill tone={(item.demand_signal || 'High') === 'High' ? 'green' : 'orange'}>
                            {item.demand_signal || 'High'}
                          </Pill>
                        </td>
                        <td className="space-x-2">
                          <button type="button" onClick={() => watch(item)} className="text-blue-400">
                            Watch
                          </button>
                          <a href={`/listing-composer?niche=${encodeURIComponent(item.keyword || item.name)}`} className="text-orange-300">
                            Compose
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>

            <Panel title="Suggestions & Inspiration">
              <div className="space-y-4">
                <div>
                  <p className="mb-2 text-sm font-medium">Phrase Suggestions</p>
                  <div className="flex flex-wrap gap-2">
                    {(data.phrase_suggestions || []).map((phrase: string) => <Pill key={phrase}>{phrase}</Pill>)}
                  </div>
                </div>
                <div>
                  <p className="mb-2 text-sm font-medium">Design Inspiration</p>
                  <div className="grid grid-cols-2 gap-2">
                    {(data.design_inspiration || []).slice(0, 4).map((idea: any) => (
                      <div key={idea.title} className="flex aspect-square items-center justify-center rounded-md border border-slate-800 bg-slate-950 p-2 text-center text-xs text-orange-300">
                        {idea.title}
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-2 text-sm font-medium">Related Niches</p>
                  <div className="flex flex-wrap gap-2">
                    {(data.related_niches || []).map((item: string) => <Pill key={item}>{item}</Pill>)}
                  </div>
                </div>
              </div>
            </Panel>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            <Panel title="Saved Searches">
              <div className="space-y-2">
                {(data.saved_searches || []).map((item: any) => (
                  <div key={`${item.id}-${item.name}`} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                    <p className="font-medium">{item.name}</p>
                    <p className="text-slate-500">{item.query} - {item.result_count} results</p>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Recent Queries">
              <div className="space-y-2 text-sm">
                {(data.recent_queries || []).map((item: any) => (
                  <div key={item.query} className="flex justify-between">
                    <span>{item.query}</span>
                    <span className="text-slate-500">{item.age}</span>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Top Result Comparison">
              <div className="grid grid-cols-3 gap-2">
                {(data.comparison || results).slice(0, 3).map((item: any, index: number) => (
                  <div key={`${item.id}-${index}`} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-xs">
                    <Pill tone="orange">#{index + 1}</Pill>
                    <p className="mt-2 font-medium text-slate-100">{item.name}</p>
                    <p className="text-emerald-400">Score {item.trend_score || 80}</p>
                    <p className="text-slate-500">${item.price || '19.99'}</p>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
