import React, { ReactNode, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';

import { Metric, Provenance } from '../services/controlCenter';

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold text-slate-50">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}

type QueryValue = string | string[] | undefined;

function readQueryValue(value: QueryValue, fallback = '') {
  if (Array.isArray(value)) return value[0] ?? fallback;
  return value ?? fallback;
}

export function useQueryParamState(key: string, fallback = '') {
  const router = useRouter();
  const [value, setValue] = useState(fallback);

  useEffect(() => {
    if (!router.isReady) return;
    setValue(readQueryValue(router.query?.[key], fallback));
  }, [fallback, key, router.isReady, router.query]);

  const updateValue = (nextValue: string) => {
    setValue(nextValue);
    const nextQuery = { ...(router.query || {}) };
    if (nextValue) {
      nextQuery[key] = nextValue;
    } else {
      delete nextQuery[key];
    }
    void router.push({ pathname: router.pathname, query: nextQuery }, undefined, { shallow: true });
  };

  return [value, updateValue] as const;
}

export function useGlobalFilterQuery(defaults: Partial<Record<GlobalFilterKey, string>> = {}) {
  const [marketplace, setMarketplace] = useQueryParamState('marketplace', defaults.marketplace || 'etsy');
  const [store, setStore] = useQueryParamState('store', defaults.store || 'all');
  const [country, setCountry] = useQueryParamState('country', defaults.country || 'US');
  const [language, setLanguage] = useQueryParamState('language', defaults.language || 'en');
  const [category, setCategory] = useQueryParamState('category', defaults.category || 'all');
  const [dateStart, setDateStart] = useQueryParamState('date_start', defaults.date_start || '2025-05-12');
  const [dateEnd, setDateEnd] = useQueryParamState('date_end', defaults.date_end || '2025-05-18');

  return {
    values: { marketplace, store, country, language, category, date_start: dateStart, date_end: dateEnd },
    setters: { setMarketplace, setStore, setCountry, setLanguage, setCategory, setDateStart, setDateEnd },
  };
}

type GlobalFilterKey = 'marketplace' | 'store' | 'country' | 'language' | 'category' | 'date_start' | 'date_end';

const datePresets = [
  { label: 'May 12 - May 18, 2025', start: '2025-05-12', end: '2025-05-18' },
  { label: 'Last 7 Days', start: 'last-7', end: 'today' },
  { label: 'Last 30 Days', start: 'last-30', end: 'today' },
  { label: 'Quarter to Date', start: 'quarter-start', end: 'today' },
];

export function GlobalDateRangeControl({ className = '' }: { className?: string }) {
  const { values } = useGlobalFilterQuery();
  const router = useRouter();
  const selected = useMemo(
    () =>
      datePresets.find((preset) => preset.start === values.date_start && preset.end === values.date_end) ||
      datePresets[0],
    [values.date_end, values.date_start]
  );

  const selectPreset = (label: string) => {
    const preset = datePresets.find((item) => item.label === label) || datePresets[0];
    void router.push(
      { pathname: router.pathname, query: { ...(router.query || {}), date_start: preset.start, date_end: preset.end } },
      undefined,
      { shallow: true }
    );
  };

  return (
    <label className={`flex min-w-[210px] items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 ${className}`}>
      <CalendarIcon className="h-4 w-4 text-slate-300" />
      <span className="sr-only">Date Range</span>
      <select
        aria-label="Date Range"
        value={selected.label}
        onChange={(event) => selectPreset(event.target.value)}
        className="w-full bg-transparent text-sm outline-none"
      >
        {datePresets.map((preset) => (
          <option key={preset.label} value={preset.label} className="bg-slate-950">
            {preset.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function Panel({
  title,
  children,
  action,
  className = '',
}: {
  title?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-md border border-slate-800 bg-slate-900/85 ${className}`}>
      {title || action ? (
        <div className="flex items-center justify-between gap-3 border-b border-slate-800 px-3 py-2.5">
          {title ? <h2 className="text-sm font-semibold text-slate-100">{title}</h2> : <span />}
          {action}
        </div>
      ) : null}
      <div className="p-3">{children}</div>
    </section>
  );
}

export function Button({
  children,
  onClick,
  variant = 'secondary',
  type = 'button',
  disabled = false,
  loading = false,
  success = false,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  type?: 'button' | 'submit';
  disabled?: boolean;
  loading?: boolean;
  success?: boolean;
}) {
  const styles = {
    primary: 'border-orange-500 bg-orange-500 text-white hover:bg-orange-400',
    secondary: 'border-slate-700 bg-slate-800 text-slate-100 hover:bg-slate-700',
    danger: 'border-red-500/60 bg-red-950 text-red-200 hover:bg-red-900',
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`rounded-md border px-3 py-2 text-sm font-medium transition ${styles[variant]} disabled:cursor-not-allowed disabled:opacity-60`}
    >
      <span className="inline-flex items-center gap-2">
        {loading ? <SpinnerIcon className="h-4 w-4 animate-spin" /> : null}
        {success ? <CheckIcon className="h-4 w-4 text-emerald-300" /> : null}
        {children}
      </span>
    </button>
  );
}

export function MetricGrid({ metrics }: { metrics: Metric[] }) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {metrics.map((metric) => (
        <MetricCard key={metric.label} metric={metric} />
      ))}
    </div>
  );
}

export function MetricCard({ metric }: { metric: Metric }) {
  const delta = Number(metric.delta || 0);
  const isPositive = delta >= 0;
  return (
    <Panel className="min-h-[112px]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium text-slate-300">{metric.label}</p>
          <div className="mt-2 flex items-end gap-1">
            <span className="text-2xl font-semibold text-slate-50">{formatNumber(metric.value)}</span>
            {metric.unit ? <span className="pb-1 text-sm text-slate-400">{metric.unit}</span> : null}
          </div>
        </div>
        <span className="rounded-full border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-orange-300">
          {metric.provenance?.is_estimated ? 'Est' : 'Live'}
        </span>
      </div>
      <div className="mt-2 flex items-center justify-between gap-3">
        <p className={`text-xs ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
          {isPositive ? '+' : ''}
          {delta}
          {metric.unit || '%'} vs last 7 days
        </p>
        <Sparkline values={metric.sparkline || []} />
      </div>
      {metric.quota ? <ProgressBar value={Number(metric.quota.percent ?? 0)} /> : null}
    </Panel>
  );
}

export function Sparkline({ values }: { values: number[] }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const points = values
    .map((value, index) => {
      const x = (index / Math.max(1, values.length - 1)) * 90 + 5;
      const y = 35 - (value / max) * 30 + 3;
      return `${x},${y}`;
    })
    .join(' ');
  return (
    <svg aria-hidden="true" className="h-10 w-28" viewBox="0 0 100 42">
      <polyline fill="none" stroke="rgb(249 115 22)" strokeWidth="2" points={points} />
    </svg>
  );
}

export function ProgressBar({ value, tone = 'orange' }: { value: number; tone?: 'orange' | 'blue' | 'green' | 'purple' }) {
  const colors = {
    orange: 'bg-orange-500',
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    purple: 'bg-purple-500',
  };
  return (
    <div className="mt-3 h-2 overflow-hidden rounded bg-slate-800">
      <div className={`h-full ${colors[tone]}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

export function Pill({
  children,
  tone = 'slate',
}: {
  children: ReactNode;
  tone?: 'slate' | 'green' | 'orange' | 'red' | 'blue' | 'purple';
}) {
  const styles = {
    slate: 'border-slate-700 bg-slate-800 text-slate-300',
    green: 'border-emerald-500/30 bg-emerald-950 text-emerald-300',
    orange: 'border-orange-500/30 bg-orange-950 text-orange-300',
    red: 'border-red-500/30 bg-red-950 text-red-300',
    blue: 'border-blue-500/30 bg-blue-950 text-blue-300',
    purple: 'border-purple-500/30 bg-purple-950 text-purple-300',
  };
  return <span className={`rounded-md border px-2 py-1 text-xs ${styles[tone]}`}>{children}</span>;
}

export function FilterBar({ children }: { children: ReactNode }) {
  return <div className="mb-4 flex flex-wrap items-center gap-2">{children}</div>;
}

export function GlobalFilterBar({
  showDate = true,
  showStore = true,
  showMarketplace = true,
  showCountry = true,
  showLanguage = true,
  showCategory = true,
}: {
  showDate?: boolean;
  showStore?: boolean;
  showMarketplace?: boolean;
  showCountry?: boolean;
  showLanguage?: boolean;
  showCategory?: boolean;
}) {
  const { values, setters } = useGlobalFilterQuery();

  return (
    <FilterBar>
      {showMarketplace ? (
        <SelectBox label="Marketplace" value={values.marketplace} onChange={setters.setMarketplace} options={['etsy', 'Amazon US']} />
      ) : null}
      {showDate ? <GlobalDateRangeControl /> : null}
      {showStore ? <SelectBox label="Store" value={values.store} onChange={setters.setStore} options={['all', 'podpusher-etsy']} /> : null}
      {showCategory ? (
        <SelectBox label="Category" value={values.category} onChange={setters.setCategory} options={['all', 'Apparel', 'Drinkware', 'Mugs', 'Bags']} />
      ) : null}
      {showCountry ? <SelectBox label="Country" value={values.country} onChange={setters.setCountry} options={['US', 'CA', 'GB', 'DE', 'FR']} /> : null}
      {showLanguage ? <SelectBox label="Language" value={values.language} onChange={setters.setLanguage} options={['en', 'es', 'fr', 'de']} /> : null}
    </FilterBar>
  );
}

export function SelectBox({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="flex min-w-[160px] flex-col gap-1 rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-400">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="bg-transparent text-sm text-slate-100 outline-none"
      >
        {options.map((option) => (
          <option key={option} value={option} className="bg-slate-950">
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

export function TextInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="flex min-w-[220px] flex-1 flex-col gap-1 rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-400">
      {label || 'Search'}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
      />
    </label>
  );
}

export function ActionBar({ children, align = 'end' }: { children: ReactNode; align?: 'start' | 'end' | 'between' }) {
  const alignment = {
    start: 'justify-start',
    end: 'justify-end',
    between: 'justify-between',
  };
  return (
    <div className={`flex flex-wrap items-center gap-2 border-t border-slate-800 bg-slate-950/40 px-4 py-3 ${alignment[align]}`}>
      {children}
    </div>
  );
}

export function DetailDrawer({
  title,
  children,
  open,
  onClose,
  actions,
}: {
  title: string;
  children: ReactNode;
  open: boolean;
  onClose: () => void;
  actions?: ReactNode;
}) {
  if (!open) return null;
  return (
    <aside
      aria-label={title}
      className="fixed inset-y-0 right-0 z-30 flex w-full max-w-md flex-col border-l border-slate-700 bg-slate-950 shadow-2xl shadow-black/40"
    >
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <h2 className="text-base font-semibold text-slate-50">{title}</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close detail panel"
          className="rounded-md border border-slate-700 bg-slate-900 p-2 text-slate-300 hover:bg-slate-800"
        >
          <CloseIcon className="h-4 w-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">{children}</div>
      {actions ? <ActionBar>{actions}</ActionBar> : null}
    </aside>
  );
}

export function StatePanel({
  state,
  title,
  message,
  action,
}: {
  state: 'loading' | 'empty' | 'error' | 'disabled' | 'success';
  title?: string;
  message: string;
  action?: ReactNode;
}) {
  const styles = {
    loading: 'border-blue-500/30 bg-blue-950/30 text-blue-200',
    empty: 'border-slate-700 bg-slate-900 text-slate-300',
    error: 'border-red-500/40 bg-red-950/35 text-red-200',
    disabled: 'border-slate-800 bg-slate-900/60 text-slate-500',
    success: 'border-emerald-500/35 bg-emerald-950/30 text-emerald-200',
  };
  const icons = {
    loading: <SpinnerIcon className="h-4 w-4 animate-spin" />,
    empty: <InfoIcon className="h-4 w-4" />,
    error: <AlertIcon className="h-4 w-4" />,
    disabled: <LockIcon className="h-4 w-4" />,
    success: <CheckIcon className="h-4 w-4" />,
  };

  return (
    <div role={state === 'error' ? 'alert' : 'status'} className={`rounded-md border p-4 text-sm ${styles[state]}`}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5">{icons[state]}</span>
        <div className="min-w-0 flex-1">
          {title ? <p className="font-medium">{title}</p> : null}
          <p className={title ? 'mt-1' : ''}>{message}</p>
          {action ? <div className="mt-3">{action}</div> : null}
        </div>
      </div>
    </div>
  );
}

export function ProvenanceNote({ provenance }: { provenance?: Provenance }) {
  if (!provenance) return null;
  return (
    <p className="mt-3 text-xs text-slate-500">
      Source: {provenance.source}
      {provenance.is_estimated ? ' (estimated)' : ' (live)'} confidence{' '}
      {Math.round(provenance.confidence * 100)}%
    </p>
  );
}

export function EmptyState({ message }: { message: string }) {
  return <StatePanel state="empty" message={message} />;
}

export function LoadingState() {
  return <StatePanel state="loading" message="Loading dashboard data..." />;
}

export function formatNumber(value: number | string) {
  if (typeof value === 'string') return value;
  return new Intl.NumberFormat('en-US').format(value);
}

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3M5 11h14M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" />
    </svg>
  );
}

function SpinnerIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4Z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m5 13 4 4L19 7" />
    </svg>
  );
}

function CloseIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18 18 6M6 6l12 12" />
    </svg>
  );
}

function InfoIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 17v-6m0-4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}

function AlertIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v4m0 4h.01M10.3 3.9 2.7 17a2 2 0 0 0 1.7 3h15.2a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
    </svg>
  );
}

function LockIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 11V8a4 4 0 0 1 8 0v3m-9 0h10a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1Z" />
    </svg>
  );
}
