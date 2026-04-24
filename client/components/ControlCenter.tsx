import React, { ReactNode } from 'react';

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
    <section className={`rounded-lg border border-slate-800 bg-slate-900/85 ${className}`}>
      {title || action ? (
        <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
          {title ? <h2 className="text-sm font-semibold text-slate-100">{title}</h2> : <span />}
          {action}
        </div>
      ) : null}
      <div className="p-4">{children}</div>
    </section>
  );
}

export function Button({
  children,
  onClick,
  variant = 'secondary',
  type = 'button',
  disabled = false,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  type?: 'button' | 'submit';
  disabled?: boolean;
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
      disabled={disabled}
      className={`rounded-md border px-3 py-2 text-sm font-medium transition ${styles[variant]} disabled:cursor-not-allowed disabled:opacity-60`}
    >
      {children}
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
    <Panel className="min-h-[132px]">
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
      <div className="mt-3 flex items-center justify-between gap-3">
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
  return <div className="rounded-md border border-slate-800 bg-slate-900 p-4 text-sm text-slate-400">{message}</div>;
}

export function LoadingState() {
  return <div className="rounded-md border border-slate-800 bg-slate-900 p-4 text-sm text-slate-400">Loading dashboard data...</div>;
}

export function formatNumber(value: number | string) {
  if (typeof value === 'string') return value;
  return new Intl.NumberFormat('en-US').format(value);
}
