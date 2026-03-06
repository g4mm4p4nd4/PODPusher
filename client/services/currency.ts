/**
 * ICU Currency Formatting Utility
 *
 * Provides locale-aware currency formatting using Intl.NumberFormat.
 * Supports all locales configured in next-i18next.config.js.
 *
 * Owner: Frontend-Coder (per DEVELOPMENT_PLAN.md Task 1.1.4)
 * Reference: Frontend-Coder §7 (Internationalisation)
 */

export type SupportedCurrency = 'USD' | 'EUR' | 'GBP' | 'CAD' | 'AUD';

/** Map locales to their default currencies. */
const LOCALE_CURRENCY_MAP: Record<string, SupportedCurrency> = {
  en: 'USD',
  es: 'EUR',
  fr: 'EUR',
  de: 'EUR',
};

/**
 * Format a monetary value according to the user's locale and currency.
 *
 * @param amount  - The numeric amount to format.
 * @param locale  - BCP 47 locale string (e.g. 'en', 'fr', 'de').
 * @param currency - ISO 4217 currency code. Defaults based on locale.
 * @returns Formatted currency string (e.g. "$12.99", "12,99 €").
 */
export function formatCurrency(
  amount: number,
  locale: string = 'en',
  currency?: SupportedCurrency,
): string {
  const resolvedCurrency = currency ?? LOCALE_CURRENCY_MAP[locale] ?? 'USD';
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: resolvedCurrency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    // Fallback for environments without full Intl support
    return `${resolvedCurrency} ${amount.toFixed(2)}`;
  }
}

/**
 * Format a compact number (e.g. 1.2K, 3.4M) for display in dashboards.
 *
 * @param value  - The numeric value.
 * @param locale - BCP 47 locale string.
 * @returns Compact formatted string.
 */
export function formatCompactNumber(value: number, locale: string = 'en'): string {
  try {
    return new Intl.NumberFormat(locale, {
      notation: 'compact',
      compactDisplay: 'short',
    }).format(value);
  } catch {
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return String(value);
  }
}

/**
 * Get the default currency for a locale.
 */
export function getDefaultCurrency(locale: string): SupportedCurrency {
  return LOCALE_CURRENCY_MAP[locale] ?? 'USD';
}
