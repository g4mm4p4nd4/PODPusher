export function formatCurrency(value: number, locale: string, currency = 'USD'): string {
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(value);
  } catch (error) {
    console.warn('formatCurrency fallback', error);
    return `${currency} ${value.toFixed(2)}`;
  }
}
