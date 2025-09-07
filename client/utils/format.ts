export function formatNumber(value: number, locale?: string) {
  return new Intl.NumberFormat(locale).format(value);
}

export function formatCurrency(value: number, currency: string = 'USD', locale?: string) {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(value);
}

export function formatPercent(value: number, locale?: string) {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatDate(date: string | number | Date, locale?: string) {
  return new Intl.DateTimeFormat(locale).format(new Date(date));
}
