import React from 'react';
import { useRouter } from 'next/router';

export default function LanguageSwitcher() {
  const router = useRouter();
  const { locale, locales, pathname, query, asPath } = router;

  const changeLocale = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLocale = e.target.value;
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
          {l.toUpperCase()}
        </option>
      ))}
    </select>
  );
}
