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
import { DemoProductArt, variantForText } from '../components/DemoProductArt';
import {
  DashboardResponse,
  addToWatchlist,
  fetchSearchInsights,
  generateSearchTags,
  saveSearch,
} from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [rating, setRating] = useState('4');
  const [priceBand, setPriceBand] = useState('$10-$25');
  const [marketplace, setMarketplace] = useState('etsy');
  const [season, setSeason] = useState('Summer');
  const [niche, setNiche] = useState('all');
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [generatedTags, setGeneratedTags] = useState<string[]>([]);
  const [status, setStatus] = useState('');
  const results = (data?.results || data?.items || []) as any[];
  const selectedItems = results.filter((item) => selectedIds.includes(itemKey(item)));

  const runSearch = async () => {
    setLoading(true);
    const raw = await fetchSearchInsights({
      q: query,
      category: category === 'all' ? undefined : category,
      rating_min: rating,
      price_band: priceBand,
      marketplace,
      season,
      niche: niche === 'all' ? undefined : niche,
    });
    setData(raw);
    setSelectedItem((raw.results || raw.items || [])[0] || null);
    setLoading(false);
  };

  useEffect(() => {
    if (router.query.q) {
      setQuery(String(router.query.q));
    }
    if (router.query.category) setCategory(String(router.query.category));
    if (router.query.marketplace) setMarketplace(String(router.query.marketplace));
    if (router.query.season) setSeason(String(router.query.season));
    if (router.query.niche) setNiche(String(router.query.niche));
  }, [router.query]);

  useEffect(() => {
    void runSearch();
  }, []);

  const saveCurrentSearch = async () => {
    await saveSearch({
      name: query || 'Current Search',
      query,
      filters: { category, rating, price_band: priceBand, marketplace, season, niche },
      result_count: results.length,
    });
    setStatus('Search saved');
    await runSearch();
  };

  const watch = async (item: any) => {
    await addToWatchlist({ item_type: 'product', name: item.name, context: item });
    setStatus(`Added ${item.name} to watchlist`);
  };

  const addSelectedToWatchlist = async () => {
    const items = selectedItems.length ? selectedItems : selectedItem ? [selectedItem] : [];
    await Promise.all(items.map((item) => addToWatchlist({ item_type: 'product', name: item.name, context: item })));
    setStatus(`${items.length} item${items.length === 1 ? '' : 's'} added to watchlist`);
  };

  const composerHref = (item = selectedItems[0] || selectedItem) => {
    if (!item) return '/listing-composer';
    const params = new URLSearchParams({
      source: 'search',
      niche: niche === 'all' ? item.keyword || item.name : niche,
      keyword: item.keyword || item.name,
      product_type: item.category || category,
      audience: niche === 'all' ? 'Marketplace Buyers' : niche,
      tags: generatedTags.length ? generatedTags.join(',') : [item.keyword, item.category, season].filter(Boolean).join(','),
    });
    return `/listing-composer?${params.toString()}`;
  };

  const sendToComposer = (item = selectedItems[0] || selectedItem) => {
    if (!item) return;
    void router.push(composerHref(item));
  };

  const generateTags = async (item = selectedItems[0] || selectedItem) => {
    if (!item) return;
    setStatus(`Generating tags for ${item.name}...`);
    const tags = await generateSearchTags({
      title: item.name,
      description: `${item.keyword || query} ${item.category || category} ${season} ${niche}`,
    });
    setGeneratedTags(tags);
    setStatus(`Generated ${tags.length} tags`);
  };

  const reuseQuery = (item: any) => {
    setQuery(item.query);
    setStatus(`Loaded recent query: ${item.query}`);
  };

  const toggleSelected = (item: any) => {
    const key = itemKey(item);
    setSelectedItem(item);
    setSelectedIds((current) =>
      current.includes(key) ? current.filter((id) => id !== key) : [...current, key].slice(0, 3)
    );
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Search & Suggestions"
        actions={
          <>
            {status ? <span className="text-sm text-emerald-400" role="status">{status}</span> : null}
            <Button onClick={saveCurrentSearch}>Save Search</Button>
          </>
        }
      />
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void runSearch();
        }}
      >
        <FilterBar>
          <TextInput label="Keyword" value={query} onChange={setQuery} placeholder="Keyword" />
          <SelectBox label="Category" value={category} onChange={setCategory} options={['all', 'Apparel', 'Drinkware', 'Mugs', 'Bags']} />
          <SelectBox label="Rating" value={rating} onChange={setRating} options={['all', '3', '4', '4.5']} />
          <SelectBox label="Price Band" value={priceBand} onChange={setPriceBand} options={['all', '$0-$10', '$10-$25', '$25-$50', '$50+']} />
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
                      <th>Thumbnail</th>
                      <th>Select</th>
                      <th>Category</th>
                      <th>Rating</th>
                      <th>Trend Score</th>
                      <th>Demand Signal</th>
                      <th>Quick Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((item) => (
                      <tr
                        key={item.id || item.name}
                        onClick={() => setSelectedItem(item)}
                        className={`cursor-pointer border-t border-slate-800 ${selectedItem?.name === item.name ? 'bg-blue-500/10' : ''}`}
                      >
                        <td className="py-3 font-medium text-slate-100">{item.name}</td>
                        <td className="min-w-[150px]">
                          <DemoProductArt
                            title={item.name}
                            subtitle={`${item.category || 'Product'} - $${item.price || '19.99'}`}
                            productType={item.category}
                            variant={variantForText(`${item.name} ${item.keyword || ''}`)}
                            compact
                          />
                        </td>
                        <td>
                          <input
                            aria-label={`Select ${item.name}`}
                            type="checkbox"
                            checked={selectedIds.includes(itemKey(item))}
                            onChange={() => toggleSelected(item)}
                            onClick={(event) => event.stopPropagation()}
                          />
                        </td>
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
                          <a href={composerHref(item)} className="text-orange-300">
                            Compose
                          </a>
                          <button type="button" onClick={() => generateTags(item)} className="text-emerald-300">
                            Tags
                          </button>
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
                  {generatedTags.length ? (
                    <>
                      <p className="mb-2 mt-4 text-sm font-medium">Generated Tags</p>
                      <div className="flex flex-wrap gap-2" aria-label="Generated Tags">
                        {generatedTags.map((tag) => <Pill key={tag} tone="green">{tag}</Pill>)}
                      </div>
                    </>
                  ) : null}
                </div>
                <div>
                  <p className="mb-2 text-sm font-medium">Design Inspiration</p>
                  <div className="grid grid-cols-2 gap-2">
                    {((data.design_inspiration || []).length
                      ? data.design_inspiration
                      : results.map((item) => ({ title: item.name, product_type: item.category }))
                    ).slice(0, 4).map((idea: any) => (
                      <DemoProductArt
                        key={idea.title}
                        title={idea.title}
                        subtitle={idea.product_type || 'Search concept'}
                        productType={idea.product_type || 'Product'}
                        variant={variantForText(idea.title)}
                        compact
                      />
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-2 text-sm font-medium">Related Niches</p>
                  <div className="flex flex-wrap gap-2">
                    {(data.related_niches || []).map((item: string) => (
                      <button key={item} type="button" onClick={() => setNiche(item)}>
                        <Pill>{item}</Pill>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </Panel>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            <Panel title="Saved Searches">
              <div className="space-y-2">
                {(data.saved_searches || []).map((item: any) => (
                  <button
                    key={`${item.id}-${item.name}`}
                    type="button"
                    onClick={() => {
                      setQuery(item.query);
                      setCategory(item.filters?.category || 'all');
                      setMarketplace(item.filters?.marketplace || 'etsy');
                      setSeason(item.filters?.season || 'Summer');
                      setNiche(item.filters?.niche || 'all');
                    }}
                    className="w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-left text-sm"
                  >
                    <p className="font-medium">{item.name}</p>
                    <p className="text-slate-500">{item.query} - {item.result_count} results</p>
                  </button>
                ))}
              </div>
            </Panel>
            <Panel title="Recent Queries">
              <div className="space-y-2 text-sm">
                {(data.recent_queries || []).map((item: any) => (
                  <button key={item.query} type="button" onClick={() => reuseQuery(item)} className="flex w-full justify-between text-left">
                    <span>{item.query}</span>
                    <span className="text-slate-500">{item.age}</span>
                  </button>
                ))}
              </div>
            </Panel>
            <Panel title={`Top Result Comparison (${selectedItems.length || Math.min(3, results.length)} selected)`}>
              <div className="grid grid-cols-3 gap-2">
                {(selectedItems.length ? selectedItems : data.comparison || results).slice(0, 3).map((item: any, index: number) => (
                  <div key={`${item.id}-${index}`} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-xs">
                    <DemoProductArt
                      title={item.name}
                      subtitle={item.category || 'Compared result'}
                      productType={item.category}
                      variant={variantForText(`${item.name} ${item.keyword || ''}`)}
                      compact
                      className="mb-2"
                    />
                    <Pill tone="orange">#{index + 1}</Pill>
                    <p className="mt-2 font-medium text-slate-100">{item.name}</p>
                    <p className="text-emerald-400">Score {item.trend_score || 80}</p>
                    <p className="text-slate-500">${item.price || '19.99'}</p>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
          <div className="sticky bottom-0 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/95 p-4">
            <span className="text-sm text-slate-300">{selectedItems.length} items selected</span>
            <div className="flex flex-wrap gap-2">
              <Button onClick={addSelectedToWatchlist}>Add to Watchlist</Button>
              <a
                href={composerHref()}
                className="rounded-md border border-orange-500 bg-orange-500 px-3 py-2 text-sm font-medium text-white transition hover:bg-orange-400"
              >
                Send to Composer
              </a>
              <Button onClick={() => generateTags()}>Generate Tags</Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function itemKey(item: any) {
  return String(item.id || item.name);
}

export const getStaticProps = getCommonStaticProps;
