import { useRouter } from 'next/router';
import React, { useEffect, useMemo, useState } from 'react';

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
  TextInput,
} from '../components/ControlCenter';
import { DemoProductArt, variantForText } from '../components/DemoProductArt';
import { DashboardResponse, abAction, createABTest, fetchABDashboard } from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

type ABVariant = {
  id: number;
  name: string;
  weight: number;
  impressions: number;
  clicks: number;
  ctr: number;
};

type ABExperiment = {
  id: number;
  name: string;
  product_id?: number | null;
  product: string;
  experiment_type: string;
  status: string;
  start_time?: string | null;
  end_time?: string | null;
  impressions: number;
  clicks: number;
  ctr: number;
  ctr_lift: number;
  confidence: number;
  significant: boolean;
  winner?: ABVariant | null;
  variants: ABVariant[];
  insights: string[];
  integration_status?: { listing_push?: string; message?: string };
  provenance?: DashboardResponse;
};

type ProductOption = {
  id: number;
  name: string;
};

const variableOptions = [
  { value: 'title', label: 'Title' },
  { value: 'thumbnail', label: 'Thumbnail' },
  { value: 'tags', label: 'Tags' },
  { value: 'description', label: 'Description' },
  { value: 'image', label: 'Image' },
  { value: 'price', label: 'Price' },
];

const statusOptions = ['all', 'running', 'paused', 'completed', 'pushed'];

export default function ABTestingLabPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [actionState, setActionState] = useState<string>('');
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    start_date: '',
    end_date: '',
  });
  const [form, setForm] = useState({
    name: '',
    product_id: '',
    experiment_type: 'title',
    variant_a: '',
    variant_b: '',
    split: '50/50',
  });

  const experiments: ABExperiment[] = data?.experiments || [];
  const selected = useMemo(
    () => experiments.find((test) => test.id === selectedId) || experiments[0] || null,
    [experiments, selectedId]
  );
  const products: ProductOption[] = data?.product_options || [];

  const load = async (preferredId?: number | null) => {
    setLoading(true);
    const result = await fetchABDashboard({
      search: filters.search || undefined,
      status: filters.status === 'all' ? undefined : filters.status,
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
    });
    setData(result);
    const ids = (result.experiments || []).map((item: ABExperiment) => item.id);
    setSelectedId(ids.includes(preferredId as number) ? preferredId || null : ids[0] ?? null);
    setLoading(false);
  };

  useEffect(() => {
    const queryProductId = typeof router.query.product_id === 'string' ? router.query.product_id : '';
    const queryProduct = typeof router.query.product === 'string' ? router.query.product : '';
    const queryVariable = typeof router.query.variable === 'string' ? router.query.variable : '';
    setForm((current) => ({
      ...current,
      product_id: queryProductId || current.product_id,
      name: queryProduct && !current.name ? `${queryProduct} Test` : current.name,
      experiment_type: variableOptions.some((option) => option.value === queryVariable)
        ? queryVariable
        : current.experiment_type,
    }));
  }, [router.query.product, router.query.product_id, router.query.variable]);

  useEffect(() => {
    void load(selectedId);
  }, [filters.search, filters.status, filters.start_date, filters.end_date]);

  const submitCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.name || !form.product_id || !form.variant_a || !form.variant_b) return;
    setCreating(true);
    setActionState('');
    const [left, right] = form.split.split('/').map((value) => Number(value) / 100);
    const created = await createABTest({
      name: form.name,
      product_id: Number(form.product_id),
      experiment_type: form.experiment_type,
      variants: [
        { name: form.variant_a, weight: left },
        { name: form.variant_b, weight: right },
      ],
    });
    setForm((current) => ({ ...current, name: '', variant_a: '', variant_b: '' }));
    setActionState('Created A/B test in local experiment state.');
    setCreating(false);
    await load(created.id as number);
  };

  const patchSelected = (patch: Partial<ABExperiment>) => {
    if (!selected) return;
    setData((current) => {
      if (!current) return current;
      return {
        ...current,
        experiments: (current.experiments || []).map((test: ABExperiment) =>
          test.id === selected.id ? { ...test, ...patch } : test
        ),
      };
    });
  };

  const runAction = async (action: 'pause' | 'duplicate' | 'end' | 'push-winner') => {
    if (!selected || selected.id === undefined) return;
    setActionState('');
    const result = await abAction(selected.id, action);
    if (result.demo_state) {
      if (action === 'duplicate') {
        setData((current) =>
          current
            ? {
                ...current,
                experiments: [...(current.experiments || []), result],
              }
            : current
        );
        setSelectedId(result.id);
      } else {
        patchSelected({
          status: result.status,
          winner: selected.winner,
          integration_status: result.integration_status || selected.integration_status,
        });
      }
      setActionState(result.integration_status?.message || 'Demo state updated for this action.');
      return;
    }
    setActionState(
      action === 'push-winner'
        ? result.integration_status?.message || 'Winning variant marked for listing update.'
        : 'Experiment state updated.'
    );
    await load(action === 'duplicate' ? result.id : selected.id);
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="A/B Testing Lab"
        actions={<Button variant="primary" onClick={() => document.getElementById('create-ab-test')?.scrollIntoView()}>Create A/B Test</Button>}
      />
      {loading || !data ? (
        <LoadingState />
      ) : (
        <>
          <MetricGrid metrics={data.cards || []} />
          <Panel title="Experiments">
            <FilterBar>
              <TextInput
                label="Search tests"
                placeholder="Search tests, products, variables..."
                value={filters.search}
                onChange={(search) => setFilters((current) => ({ ...current, search }))}
              />
              <SelectBox
                label="Status"
                value={filters.status}
                onChange={(status) => setFilters((current) => ({ ...current, status }))}
                options={statusOptions}
              />
              <DateFilter
                label="Start"
                value={filters.start_date}
                onChange={(start_date) => setFilters((current) => ({ ...current, start_date }))}
              />
              <DateFilter
                label="End"
                value={filters.end_date}
                onChange={(end_date) => setFilters((current) => ({ ...current, end_date }))}
              />
            </FilterBar>
            {experiments.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="text-left text-slate-500">
                    <tr>
                      <th className="py-2">Test Name</th>
                      <th>Product</th>
                      <th>Asset</th>
                      <th>Variable</th>
                      <th>Start Date</th>
                      <th>Impressions</th>
                      <th>Clicks</th>
                      <th>CTR</th>
                      <th>Status</th>
                      <th>Winner</th>
                    </tr>
                  </thead>
                  <tbody>
                    {experiments.map((test) => (
                      <tr
                        key={test.id}
                        onClick={() => setSelectedId(test.id)}
                        className={`cursor-pointer border-t border-slate-800 ${
                          selected?.id === test.id ? 'bg-orange-500/10' : ''
                        }`}
                      >
                        <td className="py-3 font-medium text-slate-100">
                          {test.name}
                          <span className="block text-xs text-slate-500">#{test.id}</span>
                        </td>
                        <td>{test.product}</td>
                        <td className="min-w-[140px]">
                          <DemoProductArt
                            title={test.product}
                            subtitle={`${labelForVariable(test.experiment_type)} test`}
                            productType={labelForVariable(test.experiment_type)}
                            variant={variantForText(test.product)}
                            compact
                          />
                        </td>
                        <td>{labelForVariable(test.experiment_type)}</td>
                        <td>{formatDate(test.start_time)}</td>
                        <td>{formatNumber(test.impressions)}</td>
                        <td>{formatNumber(test.clicks)}</td>
                        <td>{test.ctr}%</td>
                        <td><Pill tone={toneForStatus(test.status)}>{test.status}</Pill></td>
                        <td>{test.winner?.name || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState message="No experiments match the current filters." />
            )}
            <ProvenanceNote provenance={data.provenance} />
          </Panel>

          <div className="grid gap-4 xl:grid-cols-[0.75fr_1.45fr_0.75fr_0.55fr]">
            <Panel title="Create New Test" className="min-w-0">
              <form id="create-ab-test" onSubmit={submitCreate} className="space-y-3">
                <Field label="Test Name">
                  <input
                    value={form.name}
                    onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                    className="w-full bg-transparent text-sm text-slate-100 outline-none"
                    placeholder="Retro Sunset Tee - Title Test"
                  />
                </Field>
                <Field label="Select Product">
                  <select
                    value={form.product_id}
                    onChange={(event) => setForm((current) => ({ ...current, product_id: event.target.value }))}
                    className="w-full bg-transparent text-sm text-slate-100 outline-none"
                  >
                    <option value="" className="bg-slate-950">Select a product</option>
                    {products.map((product) => (
                      <option key={product.id} value={product.id} className="bg-slate-950">
                        {product.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <div>
                  <p className="mb-2 text-xs text-slate-400">Test Variable</p>
                  <div className="grid grid-cols-2 gap-2">
                    {variableOptions.slice(0, 4).map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setForm((current) => ({ ...current, experiment_type: option.value }))}
                        className={`rounded-md border px-3 py-2 text-left text-sm ${
                          form.experiment_type === option.value
                            ? 'border-orange-500 bg-orange-500/10 text-orange-200'
                            : 'border-slate-800 bg-slate-950 text-slate-300'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>
                <Field label="Variant A">
                  <input
                    value={form.variant_a}
                    onChange={(event) => setForm((current) => ({ ...current, variant_a: event.target.value }))}
                    className="w-full bg-transparent text-sm text-slate-100 outline-none"
                    placeholder="Control"
                  />
                </Field>
                <Field label="Variant B">
                  <input
                    value={form.variant_b}
                    onChange={(event) => setForm((current) => ({ ...current, variant_b: event.target.value }))}
                    className="w-full bg-transparent text-sm text-slate-100 outline-none"
                    placeholder="Challenger"
                  />
                </Field>
                <Field label="Traffic Split">
                  <select
                    value={form.split}
                    onChange={(event) => setForm((current) => ({ ...current, split: event.target.value }))}
                    className="w-full bg-transparent text-sm text-slate-100 outline-none"
                  >
                    <option value="50/50" className="bg-slate-950">50% / 50%</option>
                    <option value="60/40" className="bg-slate-950">60% / 40%</option>
                    <option value="70/30" className="bg-slate-950">70% / 30%</option>
                  </select>
                </Field>
                <Button type="submit" variant="primary" disabled={creating || !form.product_id || !form.variant_a || !form.variant_b}>
                  {creating ? 'Creating...' : 'Create A/B Test'}
                </Button>
              </form>
            </Panel>

            <Panel
              title={selected ? `${selected.name} - ${labelForVariable(selected.experiment_type)}` : 'Selected Experiment'}
              action={selected ? <Pill tone={toneForStatus(selected.status)}>{selected.status}</Pill> : null}
            >
              {selected ? (
                <>
                  <div className="mb-4 grid gap-3 md:grid-cols-4">
                    <Stat label="Impressions" value={formatNumber(selected.impressions)} />
                    <Stat label="Clicks" value={formatNumber(selected.clicks)} />
                    <Stat label="CTR" value={`${selected.ctr}%`} />
                    <Stat label="CTR Lift" value={`${selected.ctr_lift}%`} tone="text-emerald-400" />
                  </div>
                  <VariantChart variants={selected.variants} />
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    {selected.variants.map((variant) => (
                      <div key={`${selected.id}-${variant.name}`} className="rounded-md border border-slate-800 bg-slate-950 p-4">
                        <DemoProductArt
                          title={variant.name}
                          subtitle={`${selected.product} variant`}
                          productType={labelForVariable(selected.experiment_type)}
                          variant={variantForText(`${selected.product} ${variant.name}`)}
                          compact
                          className="mb-3"
                        />
                        <div className="mb-2 flex justify-between">
                          <span className="font-medium">{variant.name}</span>
                          <span>{variant.ctr}% CTR</span>
                        </div>
                        <ProgressBar value={variant.ctr * 12} tone={selected.winner?.name === variant.name ? 'green' : 'blue'} />
                        <p className="mt-2 text-sm text-slate-500">
                          {formatNumber(variant.impressions)} impressions - {formatNumber(variant.clicks)} clicks - {Math.round(variant.weight * 100)}% traffic
                        </p>
                      </div>
                    ))}
                  </div>
                  <ProvenanceNote provenance={selected.provenance as any} />
                </>
              ) : (
                <EmptyState message="Select an experiment to inspect variant performance." />
              )}
            </Panel>

            <div className="space-y-4">
              <Panel title="Statistical Significance">
                {selected ? (
                  <>
                    <div className="mx-auto flex h-36 w-36 items-center justify-center rounded-full border-[10px] border-emerald-500 text-center">
                      <div>
                        <div className="text-3xl font-semibold text-slate-50">{selected.confidence}%</div>
                        <div className="text-xs text-slate-400">Confidence</div>
                      </div>
                    </div>
                    <p className="mt-3 text-center text-sm text-slate-400">
                      {selected.significant ? 'Statistically significant' : 'Collect more traffic'}
                    </p>
                    <div className="mt-4 rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-300">
                      <p className="text-xs text-slate-500">Winner</p>
                      <p className="font-medium text-orange-300">{selected.winner?.name || 'Pending'}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        Probability that the winner is better than the control.
                      </p>
                    </div>
                  </>
                ) : null}
              </Panel>
              <Panel title="Insights">
                <div className="space-y-3 text-sm text-slate-300">
                  {(selected?.insights || []).map((insight) => <p key={insight}>{insight}</p>)}
                </div>
              </Panel>
            </div>

            <Panel title="Quick Actions">
              <div className="space-y-3">
                <Button onClick={() => runAction('pause')} disabled={!selected}>Pause Test</Button>
                <Button onClick={() => runAction('duplicate')} disabled={!selected}>Duplicate Test</Button>
                <Button onClick={() => runAction('end')} variant="danger" disabled={!selected}>End Test</Button>
                <Button onClick={() => runAction('push-winner')} variant="primary" disabled={!selected}>Push Winner to Listing</Button>
              </div>
              {selected?.integration_status?.message ? (
                <p className="mt-4 rounded-md border border-slate-800 bg-slate-950 p-3 text-xs text-slate-400">
                  {selected.integration_status.message}
                </p>
              ) : null}
              {actionState ? <p role="status" className="mt-3 text-xs text-emerald-300">{actionState}</p> : null}
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}

function DateFilter({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="flex min-w-[150px] flex-col gap-1 rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-400">
      {label}
      <input
        type="date"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="bg-transparent text-sm text-slate-100 outline-none"
      />
    </label>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-400">
      {label}
      <div className="mt-1">{children}</div>
    </label>
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

function VariantChart({ variants }: { variants: ABVariant[] }) {
  const maxCtr = Math.max(...variants.map((variant) => variant.ctr), 1);
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950 p-4">
      <div className="mb-3 flex items-center justify-between text-xs text-slate-500">
        <span>CTR by variant</span>
        <span>{variants.length} variants</span>
      </div>
      <div className="space-y-3">
        {variants.map((variant) => (
          <div key={variant.name} className="grid grid-cols-[110px_1fr_52px] items-center gap-3 text-sm">
            <span className="truncate text-slate-300">{variant.name}</span>
            <div className="h-3 rounded bg-slate-800">
              <div
                className="h-3 rounded bg-orange-500"
                style={{ width: `${Math.max(5, (variant.ctr / maxCtr) * 100)}%` }}
              />
            </div>
            <span className="text-right text-slate-300">{variant.ctr}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function toneForStatus(status: string): 'slate' | 'green' | 'orange' | 'red' | 'blue' | 'purple' {
  if (status === 'running') return 'green';
  if (status === 'paused') return 'orange';
  if (status === 'completed') return 'blue';
  if (status === 'pushed') return 'purple';
  return 'slate';
}

function labelForVariable(value: string) {
  return variableOptions.find((option) => option.value === value)?.label || value;
}

function formatDate(value?: string | null) {
  if (!value) return '-';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value));
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('en-US').format(value);
}

export const getStaticProps = getCommonStaticProps;
