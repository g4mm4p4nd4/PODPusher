import React, { useEffect, useState } from 'react';

import {
  Button,
  LoadingState,
  MetricGrid,
  PageHeader,
  Panel,
  Pill,
  ProgressBar,
} from '../components/ControlCenter';
import { DashboardResponse, abAction, fetchABDashboard } from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

export default function ABTestingLabPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    const result = await fetchABDashboard();
    setData(result);
    setSelected((result.experiments || [])[0] || null);
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, []);

  const runAction = async (action: 'pause' | 'duplicate' | 'end' | 'push-winner') => {
    if (!selected || !selected.id) return;
    await abAction(selected.id, action);
    await load();
  };

  return (
    <div className="space-y-4">
      <PageHeader title="A/B Testing Lab" actions={<Button variant="primary">Create A/B Test</Button>} />
      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <MetricGrid metrics={data.cards || []} />
          <Panel title="Experiments">
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="text-left text-slate-500">
                  <tr>
                    <th className="py-2">Test Name</th>
                    <th>Product</th>
                    <th>Variable</th>
                    <th>Impressions</th>
                    <th>Clicks</th>
                    <th>CTR</th>
                    <th>Status</th>
                    <th>Winner</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.experiments || []).map((test: any) => (
                    <tr
                      key={test.id}
                      onClick={() => setSelected(test)}
                      className={`cursor-pointer border-t border-slate-800 ${
                        selected?.id === test.id ? 'bg-orange-500/10' : ''
                      }`}
                    >
                      <td className="py-3 font-medium text-slate-100">{test.name}</td>
                      <td>{test.product}</td>
                      <td>{test.experiment_type}</td>
                      <td>{test.impressions}</td>
                      <td>{test.clicks}</td>
                      <td>{test.ctr}%</td>
                      <td><Pill tone={test.status === 'running' ? 'green' : 'blue'}>{test.status}</Pill></td>
                      <td>{test.winner?.name || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr_0.55fr]">
            <Panel title={selected?.name || 'Selected Experiment'}>
              {selected ? (
                <>
                  <div className="mb-4 grid gap-3 md:grid-cols-4">
                    <Stat label="Impressions" value={selected.impressions} />
                    <Stat label="Clicks" value={selected.clicks} />
                    <Stat label="CTR" value={`${selected.ctr}%`} />
                    <Stat label="CTR Lift" value={`${selected.ctr_lift}%`} tone="text-emerald-400" />
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {selected.variants.map((variant: any) => (
                      <div key={variant.name} className="rounded-md border border-slate-800 bg-slate-950 p-4">
                        <div className="mb-2 flex justify-between">
                          <span className="font-medium">{variant.name}</span>
                          <span>{variant.ctr}% CTR</span>
                        </div>
                        <ProgressBar value={variant.ctr * 12} tone="blue" />
                        <p className="mt-2 text-sm text-slate-500">
                          {variant.impressions} impressions - {variant.clicks} clicks
                        </p>
                      </div>
                    ))}
                  </div>
                </>
              ) : null}
            </Panel>

            <Panel title="Statistical Significance">
              {selected ? (
                <>
                  <div className="text-center text-5xl font-semibold text-emerald-400">{selected.confidence}%</div>
                  <p className="mt-2 text-center text-sm text-slate-400">
                    {selected.significant ? 'Statistically significant' : 'Collect more traffic'}
                  </p>
                  <div className="mt-4 space-y-2 text-sm text-slate-300">
                    {selected.insights.map((insight: string) => <p key={insight}>{insight}</p>)}
                  </div>
                </>
              ) : null}
            </Panel>

            <Panel title="Quick Actions">
              <div className="space-y-3">
                <Button onClick={() => runAction('pause')}>Pause Test</Button>
                <Button onClick={() => runAction('duplicate')}>Duplicate Test</Button>
                <Button onClick={() => runAction('end')} variant="danger">End Test</Button>
                <Button onClick={() => runAction('push-winner')} variant="primary">Push Winner to Listing</Button>
              </div>
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value, tone = 'text-slate-50' }: { label: string; value: React.ReactNode; tone?: string }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${tone}`}>{value}</p>
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
