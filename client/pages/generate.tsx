import axios from 'axios';
import { useRouter } from 'next/router';
import { useMemo, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { getAuthHeaders, resolveApiUrl } from '../services/apiBase';
import { formatCurrency } from '../utils/intl';

interface GenerateResult {
  trends?: Array<Record<string, any>>;
  ideas?: Array<Record<string, any>>;
  products?: Array<Record<string, any>>;
  listing?: Record<string, any> | null;
  auth?: { missing?: string[] };
}

export default function Generate() {
  const { t, i18n } = useTranslation('common');
  const router = useRouter();
  const [term, setTerm] = useState('');
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [loading, setLoading] = useState(false);

  const locale = router.locale ?? i18n.language ?? 'en';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post(resolveApiUrl('/generate'), { term }, { headers: getAuthHeaders() });
      setResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const trends = result?.trends ?? [];
  const ideas = result?.ideas ?? [];
  const products = result?.products ?? [];
  const listing = result?.listing;
  const missingProviders = result?.auth?.missing ?? [];
  const currency = (listing as any)?.currency ?? 'USD';

  const hasContent = useMemo(
    () => trends.length > 0 || ideas.length > 0 || products.length > 0 || !!listing,
    [trends.length, ideas.length, products.length, listing]
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('generate.title')}</h1>
      <form onSubmit={submit} className="flex gap-2 flex-wrap">
        <input
          type="text"
          className="border p-2 flex-grow min-w-[240px]"
          placeholder={t('generate.placeholder')}
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? t('loading') : t('generate.button')}
        </button>
      </form>

      {result && (
        <div className="space-y-6" data-testid="generate-results">
          {missingProviders.length > 0 && (
            <div className="rounded border border-yellow-300 bg-yellow-50 p-4 text-sm text-yellow-900">
              {t('generate.results.missingIntegrations', {
                providers: missingProviders.map((provider) => provider.toUpperCase()).join(', '),
              })}
            </div>
          )}

          {trends.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-2">{t('generate.results.trends')}</h2>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {trends.map((trend, index) => (
                  <li key={trend.term ?? trend.keyword ?? index}>
                    {trend.term ?? trend.keyword ?? t('generate.results.unknown')}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {ideas.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-2">{t('generate.results.ideas')}</h2>
              <ul className="space-y-2 text-sm">
                {ideas.map((idea, index) => (
                  <li key={idea.id ?? index} className="rounded bg-white p-3 shadow-sm">
                    <p className="font-medium">
                      {idea.title ?? idea.term ?? t('generate.results.untitled')}
                    </p>
                    {idea.description && <p className="text-gray-700">{idea.description}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h2 className="text-lg font-semibold mb-2">{t('generate.results.products')}</h2>
            {products.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">
                        {t('generate.results.description')}
                      </th>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">
                        {t('generate.results.price')}
                      </th>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">
                        {t('generate.results.tags')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {products.map((product, index) => (
                      <tr key={product.id ?? index}>
                        <td className="px-4 py-2 font-medium">
                          {product.title ?? t('generate.results.untitled')}
                        </td>
                        <td className="px-4 py-2">
                          {typeof product.price === 'number'
                            ? formatCurrency(product.price, locale, currency)
                            : t('generate.results.unknown')}
                        </td>
                        <td className="px-4 py-2 text-gray-600">
                          {Array.isArray(product.tags) && product.tags.length > 0
                            ? product.tags.join(', ')
                            : t('generate.results.none')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-600">{t('generate.results.none')}</p>
            )}
          </section>

          {listing && (
            <section className="rounded border border-gray-200 bg-white p-4 shadow-sm">
              <h2 className="text-lg font-semibold mb-2">{t('generate.results.listing')}</h2>
              {listing.title && <p className="font-medium">{listing.title}</p>}
              {listing.description && <p className="text-gray-700">{listing.description}</p>}
              {listing.listing_url && (
                <a
                  className="text-blue-600 underline"
                  href={listing.listing_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {t('generate.results.viewListing')}
                </a>
              )}
            </section>
          )}

          {!hasContent && (
            <p className="text-sm text-gray-600">{t('generate.results.noData')}</p>
          )}
        </div>
      )}
    </div>
  );
}
