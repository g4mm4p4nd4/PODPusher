import React, { useEffect, useState } from 'react';

import {
  Button,
  FilterBar,
  LoadingState,
  MetricGrid,
  PageHeader,
  Panel,
  Pill,
  ProgressBar,
  ProvenanceNote,
  SelectBox,
} from '../components/ControlCenter';
import {
  DashboardResponse,
  fetchNicheSuggestions,
  saveBrandProfile,
  saveNiche,
} from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

export default function NicheSuggestionsPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [selected, setSelected] = useState<any>(null);
  const [tone, setTone] = useState('Humorous, Positive');
  const [audience, setAudience] = useState('Adults, Parents');
  const [interest, setInterest] = useState('Pets, Coffee, Outdoors');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const result = await fetchNicheSuggestions();
    setData(result);
    setSelected((result.niches || [])[0] || null);
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, []);

  const saveProfile = async () => {
    await saveBrandProfile({
      tone,
      audience,
      interests: interest.split(',').map((item) => item.trim()).filter(Boolean),
    });
    await load();
  };

  const saveSelected = async () => {
    if (!selected) return;
    await saveNiche(selected.niche, selected.brand_fit_score);
    await load();
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Niche Suggestions"
        subtitle="Define your brand profile to get better niche suggestions."
        actions={<Button onClick={saveProfile} variant="primary">Save Profile</Button>}
      />
      <FilterBar>
        <SelectBox label="Tone" value={tone} onChange={setTone} options={['Humorous, Positive', 'Warm & Inviting', 'Minimal, Calm']} />
        <SelectBox label="Audience" value={audience} onChange={setAudience} options={['Adults, Parents', 'Teachers', 'Outdoor Buyers']} />
        <label className="flex min-w-[260px] flex-col gap-1 rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-400">
          Interests
          <input
            value={interest}
            onChange={(event) => setInterest(event.target.value)}
            className="bg-transparent text-sm text-slate-100 outline-none"
          />
        </label>
      </FilterBar>

      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <MetricGrid metrics={data.cards || []} />
          <div className="grid gap-4 xl:grid-cols-[1.35fr_0.8fr]">
            <Panel title="Suggested Niches" action={<Pill>Sort by Brand Fit Score</Pill>}>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-left text-slate-500">
                    <tr>
                      <th className="py-2">Niche</th>
                      <th>Demand Trend</th>
                      <th>Competition</th>
                      <th>Profitability</th>
                      <th>Audience</th>
                      <th>Brand Fit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data.niches || []).map((item: any) => (
                      <tr
                        key={item.niche}
                        onClick={() => setSelected(item)}
                        className={`cursor-pointer border-t border-slate-800 ${
                          selected?.niche === item.niche ? 'bg-orange-500/10' : ''
                        }`}
                      >
                        <td className="py-3 font-medium text-slate-100">{item.niche}</td>
                        <td>
                          <div className="flex h-8 items-end gap-1">
                            {item.demand_trend.map((value: number, index: number) => (
                              <span
                                key={index}
                                className="w-2 rounded-t bg-orange-500"
                                style={{ height: `${Math.max(4, value / 2)}px` }}
                              />
                            ))}
                          </div>
                        </td>
                        <td>{item.competition}/100</td>
                        <td>
                          <Pill tone={item.profitability === 'High' ? 'green' : 'orange'}>{item.profitability}</Pill>
                          <span className="ml-2 text-slate-500">${item.estimated_profit} est.</span>
                        </td>
                        <td>
                          <ProgressBar value={item.audience_overlap} tone="green" />
                        </td>
                        <td>
                          <span className="font-semibold text-slate-100">{item.brand_fit_score}</span>
                          <span className="ml-2 text-emerald-400">{item.brand_fit_label}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>

            {selected ? (
              <Panel title="Why this niche?" action={<Button onClick={saveSelected} variant="primary">Save Niche</Button>}>
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <p className="text-lg font-semibold text-slate-50">{selected.niche}</p>
                    <p className="text-sm text-slate-400">{selected.keyword}</p>
                  </div>
                  <Pill tone="green">{selected.brand_fit_score} fit</Pill>
                </div>
                <div className="space-y-3">
                  {selected.why.map((reason: string) => (
                    <div key={reason} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-300">
                      {reason}
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button onClick={saveSelected} variant="primary">Save Niche</Button>
                  <a href={`/listing-composer?niche=${encodeURIComponent(selected.niche)}`} className="rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100">
                    Create Listing
                  </a>
                </div>
              </Panel>
            ) : null}
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            <Panel title="Suggested Phrases">
              <div className="space-y-2">
                {(data.suggested_phrases || []).map((item: any) => (
                  <div key={item.phrase} className="flex justify-between rounded-md border border-slate-800 bg-slate-950 p-2 text-sm">
                    <span>{item.phrase}</span>
                    <Pill tone={item.demand === 'High' ? 'green' : 'orange'}>{item.demand}</Pill>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Design Inspiration">
              <div className="grid grid-cols-3 gap-2">
                {(data.design_inspiration || []).map((idea: any) => (
                  <div key={idea.title} className="flex aspect-[3/4] items-center justify-center rounded-md border border-slate-800 bg-slate-950 p-2 text-center text-xs text-orange-300">
                    {idea.title}
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Localized Variants">
              <div className="space-y-2 text-sm">
                {(data.localized_variants || []).map((item: any) => (
                  <div key={`${item.market}-${item.language}`} className="grid grid-cols-[90px_1fr_70px] gap-2">
                    <span className="text-slate-500">{item.market} / {item.language}</span>
                    <span>{item.phrase}</span>
                    <Pill tone={item.demand === 'High' ? 'green' : 'orange'}>{item.demand}</Pill>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
          <ProvenanceNote provenance={data.provenance} />
        </>
      )}
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
