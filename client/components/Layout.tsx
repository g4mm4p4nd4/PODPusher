import Link from 'next/link';
import { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';
import { useTranslation } from 'next-i18next';
import LanguageSwitcher from './LanguageSwitcher';
import QuotaDisplay from './QuotaDisplay';

export default function Layout({ children }: { children: ReactNode }) {
  const { t } = useTranslation('common');
  const [unread, setUnread] = useState(0);
  const [navQuery, setNavQuery] = useState('');
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const router = useRouter();

  useEffect(() => {
    axios
      .get(`${api}/api/notifications`, { headers: { 'X-User-Id': '1' } })
      .then((res) => setUnread(res.data.filter((n: any) => !n.read).length))
      .catch((err) => console.error(err));
  }, [api]);

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-gray-800 text-white p-4">
        <div className="container mx-auto flex gap-4 items-center">
          <Link href="/" className="hover:underline">{t('nav.home')}</Link>
          <Link href="/generate" className="hover:underline">{t('nav.generate')}</Link>
          <Link href="/categories" className="hover:underline">{t('nav.categories')}</Link>
          <Link href="/design" className="hover:underline">{t('nav.designIdeas')}</Link>
          <Link href="/suggestions" className="hover:underline">{t('nav.suggestions')}</Link>
          <Link href="/search" className="hover:underline">{t('nav.search')}</Link>
          <Link href="/listings" className="hover:underline">{t('nav.listings')}</Link>
          <Link href="/analytics" className="hover:underline">{t('nav.analytics')}</Link>
          <Link href="/social-generator" className="hover:underline">{t('nav.socialGenerator')}</Link>
          <Link href="/ab_tests" className="hover:underline">{t('nav.abTests')}</Link>
          <Link href="/settings" className="hover:underline">{t('nav.settings')}</Link>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              router.push(`/search?q=${encodeURIComponent(navQuery)}`);
              setNavQuery('');
            }}
            className="flex items-center ml-auto"
          >
            <input
              value={navQuery}
              onChange={(e) => setNavQuery(e.target.value)}
              placeholder={t('nav.searchPlaceholder')}
              className="p-1 rounded text-black"
            />
          </form>
          <LanguageSwitcher />
          <Link href="/schedule" className="hover:underline">
            {t('nav.schedule')}
          </Link>
          <Link
            href="/notifications"
            aria-label={t('nav.notifications')}
            className="relative flex items-center"
          >
            <span>🔔</span>
            {unread > 0 && (
              <span data-testid="unread-count" className="ml-1 text-xs bg-red-500 rounded-full px-1">
                {unread}
              </span>
            )}
          </Link>
          <QuotaDisplay />
        </div>
      </nav>
      <main className="flex-1 container mx-auto p-4">{children}</main>
    </div>
  );
}
