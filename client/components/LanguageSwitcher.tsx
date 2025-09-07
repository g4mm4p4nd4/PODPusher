import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useTranslation } from 'next-i18next';

export default function LanguageSwitcher() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const { locale, locales, pathname, query, asPath } = router;

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('locale') : null;
    if (stored && stored !== locale) {
      router.replace({ pathname, query }, asPath, { locale: stored });
    }
  }, [locale, pathname, query, asPath, router]);

  const changeLocale = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLocale = e.target.value;
    if (typeof window !== 'undefined') {
      localStorage.setItem('locale', newLocale);
    }
    router.push({ pathname, query }, asPath, { locale: newLocale });
  };

  return (
    <select
      data-testid="language-switcher"
      value={locale}
      onChange={changeLocale}
      className="ml-4 p-1 border rounded"
    >
      {locales?.map((l) => (
        <option key={l} value={l}>
          {t(`languages.${l}`)}
        </option>
      ))}
    </select>
  );
}
