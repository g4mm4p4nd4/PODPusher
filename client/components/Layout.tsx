import Link from 'next/link';
import React, { ReactNode, useState } from 'react';
import { useRouter } from 'next/router';

import LanguageSwitcher from './LanguageSwitcher';
import UserQuota from './UserQuota';

const primaryNav = [
  { href: '/', label: 'Overview', legacyLabel: 'Home', mark: 'OV' },
  { href: '/trends', label: 'Trends', mark: 'TR' },
  { href: '/seasonal-events', label: 'Seasonal Events', mark: 'SE' },
  { href: '/niches', label: 'Niches', mark: 'NI' },
  { href: '/listing-composer', label: 'Listing Composer', legacyLabel: 'Listings', mark: 'LC' },
  { href: '/search', label: 'Search & Suggestions', mark: 'SS' },
  { href: '/ab-tests', label: 'A/B Tests', mark: 'AB' },
  { href: '/notifications', label: 'Notifications & Scheduler', legacyLabel: 'Notifications', mark: 'NS' },
  { href: '/settings', label: 'Settings', mark: 'ST' },
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
  const router = useRouter();
  const pathname = router.pathname || '';

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault();
    router.push(`/search?q=${encodeURIComponent(navQuery)}`);
    setNavQuery('');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-slate-800 bg-slate-950 lg:flex lg:flex-col">
        <Link href="/" className="flex h-16 items-center border-b border-slate-800 px-5">
          <span className="mr-2 flex h-8 w-8 items-center justify-center rounded-md bg-orange-500 font-bold text-white">
            P
          </span>
          <span className="text-xl font-semibold">
            <span className="text-orange-400">POD</span>Pusher
          </span>
        </Link>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {primaryNav.map((item) => {
            const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.legacyLabel || item.label}
                aria-current={active ? 'page' : undefined}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                  active
                    ? 'bg-orange-500/15 text-orange-300'
                    : 'text-slate-300 hover:bg-slate-900 hover:text-slate-50'
                }`}
              >
                <span className="flex h-7 w-7 items-center justify-center rounded border border-slate-700 text-[10px]">
                  {item.mark}
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
        </nav>
        <div className="border-t border-slate-800 p-3">
          <UserQuota />
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
          <div className="flex h-16 items-center gap-3 px-4">
            <button
              type="button"
              className="rounded border border-slate-800 px-3 py-2 text-sm text-slate-300 lg:hidden"
            >
              Menu
            </button>
            <form onSubmit={submitSearch} className="hidden flex-1 md:block">
              <input
                value={navQuery}
                onChange={(event) => setNavQuery(event.target.value)}
                placeholder="Search keywords, niches, products..."
                className="w-full max-w-xl rounded-md border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-500"
              />
            </form>
            <select className="rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-100">
              <option>All Stores</option>
              <option>PODPusher Etsy</option>
            </select>
            <LanguageSwitcher />
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
