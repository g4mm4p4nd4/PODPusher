import React from 'react';

import { Pill } from './ControlCenter';

type DemoProductArtProps = {
  title: string;
  subtitle?: string;
  productType?: string;
  variant?: 'sunset' | 'floral' | 'teacher' | 'pickleball' | 'holiday' | 'minimal';
  compact?: boolean;
  className?: string;
};

const variantStyles = {
  sunset: {
    background: 'from-sky-950 via-rose-950 to-orange-900',
    accent: 'bg-orange-300',
    secondary: 'bg-rose-300',
  },
  floral: {
    background: 'from-emerald-950 via-slate-950 to-pink-950',
    accent: 'bg-pink-300',
    secondary: 'bg-emerald-300',
  },
  teacher: {
    background: 'from-slate-950 via-indigo-950 to-cyan-950',
    accent: 'bg-cyan-300',
    secondary: 'bg-indigo-300',
  },
  pickleball: {
    background: 'from-lime-950 via-slate-950 to-emerald-950',
    accent: 'bg-lime-300',
    secondary: 'bg-emerald-300',
  },
  holiday: {
    background: 'from-red-950 via-slate-950 to-emerald-950',
    accent: 'bg-red-300',
    secondary: 'bg-emerald-300',
  },
  minimal: {
    background: 'from-slate-900 via-slate-950 to-stone-900',
    accent: 'bg-slate-300',
    secondary: 'bg-orange-200',
  },
};

export function DemoProductArt({
  title,
  subtitle,
  productType = 'Local mockup',
  variant = 'sunset',
  compact = false,
  className = '',
}: DemoProductArtProps) {
  const style = variantStyles[variant];
  const words = title.split(/\s+/).filter(Boolean).slice(0, compact ? 3 : 5).join(' ');

  return (
    <div
      className={`relative overflow-hidden rounded-md border border-slate-700 bg-gradient-to-br ${style.background} ${className}`}
      aria-label={`${title} demo local thumbnail`}
    >
      <div className="absolute right-2 top-2 z-10">
        <Pill tone="blue">Demo / local</Pill>
      </div>
      <div className={`relative flex ${compact ? 'min-h-[86px] p-2' : 'min-h-[180px] p-4'} items-center justify-center`}>
        <div className={`absolute ${compact ? 'h-20 w-20' : 'h-32 w-32'} rounded-full ${style.accent} opacity-25 blur-sm`} />
        <div className={`absolute ${compact ? '-bottom-3 -right-2 h-16 w-16' : '-bottom-8 -right-5 h-28 w-28'} rounded-full ${style.secondary} opacity-20`} />
        <div className={`relative grid ${compact ? 'h-20 w-16' : 'h-36 w-28'} place-items-center rounded-md border border-white/15 bg-white/90 p-2 text-center shadow-2xl`}>
          <div className={`${compact ? 'text-[10px]' : 'text-xs'} font-black uppercase leading-tight text-slate-950`}>
            {(words || 'Demo design').toUpperCase()}
          </div>
          <div className={`mt-1 h-1.5 ${compact ? 'w-8' : 'w-12'} rounded-full ${style.accent}`} />
        </div>
      </div>
      <div className="border-t border-white/10 bg-slate-950/60 px-3 py-2">
        <p className={`${compact ? 'text-xs' : 'text-sm'} truncate font-medium text-slate-50`}>Local asset: {title}</p>
        <p className="truncate text-xs text-slate-400">{subtitle || productType}</p>
      </div>
    </div>
  );
}

export function variantForText(value: string): DemoProductArtProps['variant'] {
  const text = value.toLowerCase();
  if (text.includes('teacher') || text.includes('school')) return 'teacher';
  if (text.includes('pickle') || text.includes('tennis')) return 'pickleball';
  if (text.includes('holiday') || text.includes('christmas') || text.includes('mother')) return 'holiday';
  if (text.includes('floral') || text.includes('flower') || text.includes('dog')) return 'floral';
  if (text.includes('minimal') || text.includes('line')) return 'minimal';
  return 'sunset';
}
