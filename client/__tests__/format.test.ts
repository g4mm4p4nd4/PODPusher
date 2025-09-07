import { formatCurrency } from '../utils/format';

test('formats currency per locale', () => {
  expect(formatCurrency(1234.5, 'USD', 'en-US')).toBe('$1,234.50');
  const euros = formatCurrency(1234.5, 'EUR', 'es-ES');
  expect(euros).toContain('€');
  expect(euros).toContain('1234');
});
