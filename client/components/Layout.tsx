import Link from 'next/link';
import React, { ReactNode, useState } from 'react';
import { useRouter } from 'next/router';

import { GlobalDateRangeControl } from './ControlCenter';
import UserQuota from './UserQuota';

const primaryNav = [
  { href: '/', label: 'Overview', icon: HomeIcon },
  { href: '/trends', label: 'Trends', icon: TrendIcon },
  { href: '/seasonal-events', label: 'Seasonal Events', icon: CalendarIcon },
  { href: '/niches', label: 'Niches', icon: TargetIcon },
  { href: '/listing-composer', label: 'Listing Composer', icon: EditIcon },
  { href: '/search', label: 'Search & Suggestions', icon: SearchIcon },
  { href: '/ab-tests', label: 'A/B Tests', icon: FlaskIcon },
  { href: '/notifications', label: 'Notifications & Scheduler', icon: BellIcon },
  { href: '/settings', label: 'Settings', icon: GearIcon },
];

const utilityNav = [
  { href: '/generate', label: 'Generate' },
  { href: '/categories', label: 'Categories' },
  { href: '/design', label: 'Design Ideas' },
  { href: '/suggestions', label: 'Suggestions' },
  { href: '/analytics', label: 'Analytics' },
  { href: '/images', label: 'Images' },
  { href: '/schedule', label: 'Schedule' },
];

export default function Layout({ children }: { children: ReactNode }) {
  const [navQuery, setNavQuery] = useState('');
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const router = useRouter();
  const pathname = router.pathname || '';

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault();
    const term = navQuery.trim();
    const nextQuery = { ...(router.query || {}) };
    if (term) {
      nextQuery.q = term;
    } else {
      delete nextQuery.q;
    }
    router.push({ pathname: '/search', query: nextQuery });
    setNavQuery('');
  };

  const updateShellQuery = (key: string, value: string) => {
    const nextQuery = { ...(router.query || {}) };
    if (value) {
      nextQuery[key] = value;
    } else {
      delete nextQuery[key];
    }
    void router.push({ pathname: router.pathname, query: nextQuery }, undefined, { shallow: true });
  };

  const nav = (
    <>
      {primaryNav.map((item) => {
        const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-label={item.label}
            aria-current={active ? 'page' : undefined}
            className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
              active
                ? 'bg-orange-500/15 text-orange-300'
                : 'text-slate-300 hover:bg-slate-900 hover:text-slate-50'
            }`}
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-slate-700 bg-slate-900/70">
              <Icon className="h-4 w-4" />
            </span>
            <span>{item.label}</span>
          </Link>
        );
      })}
      <div className="pt-4">
        <p className="px-3 pb-2 text-xs font-semibold uppercase text-slate-500">Tools</p>
        {utilityNav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center rounded-md px-3 py-1.5 text-sm text-slate-400 transition hover:bg-slate-900 hover:text-slate-100"
          >
            {item.label}
          </Link>
        ))}
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-slate-800 bg-slate-950 lg:flex lg:flex-col">
        <Link href="/" className="flex h-16 items-center border-b border-slate-800 px-5">
          <span className="mr-2 flex h-8 w-8 items-center justify-center rounded-md bg-orange-500 text-white">
            <BrandMarkIcon className="h-5 w-5" />
          </span>
          <span className="text-xl font-semibold">
            <span className="text-orange-400">POD</span>Pusher
          </span>
        </Link>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {nav}
        </nav>
        <div className="border-t border-slate-800 p-3">
          <UserQuota />
        </div>
      </aside>
      {mobileNavOpen ? (
        <div className="fixed inset-0 z-30 bg-slate-950/90 lg:hidden">
          <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4">
            <span className="text-lg font-semibold">
              <span className="text-orange-400">POD</span>Pusher
            </span>
            <button
              type="button"
              aria-label="Close navigation"
              onClick={() => setMobileNavOpen(false)}
              className="rounded-md border border-slate-700 bg-slate-900 p-2 text-slate-200"
            >
              <CloseIcon className="h-5 w-5" />
            </button>
          </div>
          <nav className="space-y-1 px-3 py-4">{nav}</nav>
        </div>
      ) : null}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
          <div className="flex min-h-16 flex-wrap items-center gap-3 px-4 py-2">
            <button
              type="button"
              aria-label="Open navigation"
              onClick={() => setMobileNavOpen(true)}
              className="rounded-md border border-slate-800 p-2 text-slate-300 lg:hidden"
            >
              <MenuIcon className="h-5 w-5" />
            </button>
            <form onSubmit={submitSearch} className="min-w-[240px] flex-1 md:min-w-[320px]">
              <label className="flex w-full max-w-xl items-center gap-2 rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100">
                <SearchIcon className="h-4 w-4 shrink-0 text-slate-400" />
                <span className="sr-only">Global search</span>
                <input
                  value={navQuery}
                  onChange={(event) => setNavQuery(event.target.value)}
                  placeholder="Search keywords, niches, products..."
                  className="min-w-0 flex-1 bg-transparent outline-none placeholder:text-slate-500"
                />
              </label>
            </form>
            <ShellSelect
              label="Store"
              icon={StoreIcon}
              value={readQuery(router.query?.store, 'all')}
              onChange={(value) => updateShellQuery('store', value)}
              options={[
                { value: 'all', label: 'All Stores' },
                { value: 'podpusher-etsy', label: 'PODPusher Etsy' },
              ]}
            />
            <ShellSelect
              label="Marketplace"
              icon={StoreIcon}
              value={readQuery(router.query?.marketplace, 'etsy')}
              onChange={(value) => updateShellQuery('marketplace', value)}
              options={[
                { value: 'etsy', label: 'Etsy' },
                { value: 'amazon-us', label: 'Amazon US' },
              ]}
            />
            <ShellSelect
              label="Country"
              icon={GlobeIcon}
              value={readQuery(router.query?.country, 'US')}
              onChange={(value) => updateShellQuery('country', value)}
              options={[
                { value: 'US', label: 'United States' },
                { value: 'CA', label: 'Canada' },
                { value: 'GB', label: 'United Kingdom' },
              ]}
            />
            <ShellSelect
              label="Language"
              icon={GlobeIcon}
              value={readQuery(router.query?.language, 'en')}
              onChange={(value) => updateShellQuery('language', value)}
              options={[
                { value: 'en', label: 'English' },
                { value: 'es', label: 'Spanish' },
                { value: 'fr', label: 'French' },
                { value: 'de', label: 'German' },
              ]}
            />
            <GlobalDateRangeControl className="hidden xl:flex" />
            <div className="hidden border-l border-slate-800 pl-4 text-sm md:block">
              <div className="font-medium text-slate-100">Admin</div>
              <div className="text-xs text-slate-500">Administrator</div>
            </div>
          </div>
        </header>
        <main className="mx-auto min-h-[calc(100vh-4rem)] max-w-[1560px] px-4 py-5 xl:px-6">
          {children}
        </main>
      </div>
    </div>
  );
}

function readQuery(value: string | string[] | undefined, fallback: string) {
  if (Array.isArray(value)) return value[0] || fallback;
  return value || fallback;
}

function ShellSelect({
  label,
  value,
  onChange,
  options,
  icon: Icon,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  icon: ({ className }: { className?: string }) => JSX.Element;
}) {
  return (
    <label className="flex min-w-[138px] items-center gap-2 rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100">
      <Icon className="h-4 w-4 shrink-0 text-slate-300" />
      <span className="sr-only">{label}</span>
      <select
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-w-0 flex-1 bg-transparent outline-none"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value} className="bg-slate-950">
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function HomeIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M4 10.5 12 4l8 6.5V20h-5v-6H9v6H4v-9.5Z" />;
}

function TrendIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M4 16h3l4-6 4 3 5-8M16 5h4v4" />;
}

function CalendarIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M8 5V3m8 2V3M4 9h16M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Z" />;
}

function TargetIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-4a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0-3a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />;
}

function EditIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M5 19h4l10-10-4-4L5 15v4Zm10-14 4 4" />;
}

function SearchIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="m21 21-4.3-4.3M10.8 18a7.2 7.2 0 1 1 0-14.4 7.2 7.2 0 0 1 0 14.4Z" />;
}

function FlaskIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3" />;
}

function BellIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4" />;
}

function GearIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm0-12v3m0 11v3m8.5-8.5h-3m-11 0h-3m14.5-6.5-2.1 2.1m-7.8 7.8-2.1 2.1m0-12.1 2.1 2.1m7.8 7.8 2.1 2.1" />;
}

function StoreIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M4 10h16l-1-5H5l-1 5Zm1 0v10h14V10M8 20v-6h8v6" />;
}

function GlobeIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm-8-9h16M12 3c2.2 2.5 3.3 5.5 3.3 9S14.2 18.5 12 21c-2.2-2.5-3.3-5.5-3.3-9S9.8 5.5 12 3Z" />;
}

function MenuIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M4 7h16M4 12h16M4 17h16" />;
}

function CloseIcon({ className }: { className?: string }) {
  return <IconShell className={className} path="M6 18 18 6M6 6l12 12" />;
}

function BrandMarkIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M4 4.5 12 12 4 19.5v-15Zm6.5 0L20 12l-9.5 7.5V15l3.7-3-3.7-3V4.5Z" />
    </svg>
  );
}

function IconShell({ className, path }: { className?: string; path: string }) {
  return (
    <svg aria-hidden="true" className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d={path} />
    </svg>
  );
}
