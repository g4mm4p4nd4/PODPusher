import axios from 'axios';
import Link from 'next/link';
import { useRouter } from 'next/router';
import React, { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'next-i18next';
import PublishStep from '../components/PublishStep';
import { useProviders } from '../contexts/ProviderContext';
import { getAuthHeaders, resolveApiUrl } from '../services/apiBase';
import { formatCurrency } from '../utils/intl';
import { getCommonStaticProps } from '../utils/translationProps';

interface TrendItem {
  term?: string;
  keyword?: string;
}

interface IdeaItem {
  id?: number | string;
  title?: string;
  term?: string;
  description?: string;
}

interface ProductItem {
  id?: number | string;
  title?: string;
  image_url?: string;
  tags?: unknown;
  price?: number | string;
}

interface ListingItem {
  title?: string;
  description?: string;
  listing_url?: string;
  currency?: string;
}

interface GenerateResult {
  trends?: TrendItem[];
  ideas?: IdeaItem[];
  products?: ProductItem[];
  listing?: ListingItem | null;
  auth?: { missing?: string[] };
}

function ConnectionWarning() {
  const { t } = useTranslation('common');
  const { getProviderStatus } = useProviders();

  const etsyStatus = getProviderStatus('etsy');
  const printifyStatus = getProviderStatus('printify');

  const missingProviders: string[] = [];
  if (!etsyStatus.connected) missingProviders.push('Etsy');
  if (!printifyStatus.connected) missingProviders.push('Printify');

  if (missingProviders.length === 0) return null;

  return (
    <div className="mb-6 rounded-lg border border-yellow-200 bg-yellow-50 p-4">
      <div className="flex items-start gap-3">
        <svg className="mt-0.5 h-5 w-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <div className="flex-1">
          <h3 className="font-medium text-yellow-800">{t('generate.connectionRequired')}</h3>
          <p className="mt-1 text-sm text-yellow-700">
            {t('generate.connectProviders', { providers: missingProviders.join(', ') })}
          </p>
          <Link href="/settings" className="mt-2 inline-block text-sm font-medium text-yellow-800 underline hover:text-yellow-900">
            {t('generate.goToSettings')}
          </Link>
        </div>
      </div>
    </div>
  );
}

function toTags(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((tag): tag is string => typeof tag === 'string');
}

function toPrice(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

export default function Generate() {
  const { t, i18n } = useTranslation('common');
  const { allRequiredConnected, loading: providersLoading } = useProviders();
  const router = useRouter();

  const [term, setTerm] = useState('');
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [publishedProduct, setPublishedProduct] = useState<ProductItem | null>(null);

  const canGenerate = allRequiredConnected();
  const locale = router.locale ?? i18n.language ?? 'en';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canGenerate) return;

    setResult(null);
    setError(null);
    setLoading(true);

    try {
      const res = await axios.post(resolveApiUrl('/generate'), { term }, { headers: getAuthHeaders() });
      setResult(res.data);
    } catch (err) {
      const message = err instanceof Error ? err.message : t('generate.error');
      setError(message);
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
  const currency = listing?.currency ?? 'USD';
  const selectedProduct = selectedIndex >= 0 && selectedIndex < products.length ? products[selectedIndex] : null;

  const handlePublish = ({ price, tags }: { price: number; tags: string[] }) => {
    if (!selectedProduct) {
      return;
    }

    setPublishedProduct({
      ...selectedProduct,
      price,
      tags,
    });
  };

  useEffect(() => {
    if (!products.length) {
      setSelectedIndex(-1);
      setPublishedProduct(null);
      return;
    }

    if (selectedIndex >= products.length || selectedIndex < 0) {
      setSelectedIndex(0);
    }
  }, [products.length, selectedIndex]);

  const hasContent = useMemo(
    () => trends.length > 0 || ideas.length > 0 || products.length > 0 || !!listing,
    [trends.length, ideas.length, products.length, listing]
  );

  if (providersLoading) {
    return (
      <div className="space-y-6">
        <h1 className="mb-2 text-2xl font-bold">{t('generate.title')}</h1>
        <div className="animate-pulse">
          <div className="mb-4 h-10 w-full rounded bg-gray-200"></div>
          <div className="h-10 w-32 rounded bg-gray-200"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="mb-2 text-2xl font-bold">{t('generate.title')}</h1>

      <ConnectionWarning />

      <form onSubmit={submit} className="flex flex-wrap gap-2">
        <input
          type="text"
          className="min-w-[240px] flex-grow rounded border p-2"
          placeholder={t('generate.placeholder')}
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          disabled={!canGenerate || loading}
        />
        <button
          type="submit"
          disabled={!canGenerate || loading || !term.trim()}
          className="rounded bg-blue-600 px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-50 hover:bg-blue-700"
        >
          {loading ? t('generate.generating') : t('generate.button')}
        </button>
      </form>

      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

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
              <h2 className="mb-2 text-lg font-semibold">{t('generate.results.trends')}</h2>
              <ul className="list-inside list-disc space-y-1 text-sm">
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
              <h2 className="mb-2 text-lg font-semibold">{t('generate.results.ideas')}</h2>
              <ul className="space-y-2 text-sm">
                {ideas.map((idea, index) => (
                  <li key={idea.id ?? index} className="rounded bg-white p-3 shadow-sm">
                    <p className="font-medium">{idea.title ?? idea.term ?? t('generate.results.untitled')}</p>
                    {idea.description && <p className="text-gray-700">{idea.description}</p>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h2 className="mb-2 text-lg font-semibold">{t('generate.results.products')}</h2>
            {products.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">{t('generate.results.description')}</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">{t('generate.results.price')}</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">{t('generate.results.tags')}</th>
                      <th className="px-4 py-2 text-left font-medium text-gray-700">{t('generate.results.select')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {products.map((product, index) => (
                      <tr key={product.id ?? index}>
                        <td className="px-4 py-2 font-medium">{product.title ?? t('generate.results.untitled')}</td>
                        <td className="px-4 py-2">
                          {toPrice(product.price) === null
                            ? t('generate.results.unknown')
                            : formatCurrency(toPrice(product.price) ?? 0, locale, currency)}
                        </td>
                        <td className="px-4 py-2 text-gray-600">
                          {toTags(product.tags).length > 0 ? toTags(product.tags).join(', ') : t('generate.results.none')}
                        </td>
                        <td className="px-4 py-2">
                          <button
                            type="button"
                            className="rounded bg-blue-100 px-2 py-1 text-blue-700"
                            onClick={() => setSelectedIndex(index)}
                          >
                            {t('generate.results.select')}
                          </button>
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

          {selectedProduct?.image_url && (
            <section className="rounded border border-gray-200 bg-white p-4 shadow-sm">
              <h2 className="mb-2 text-lg font-semibold">{t('generate.results.publish')}</h2>
              <PublishStep
                product={{ image_url: selectedProduct.image_url }}
                onPublish={handlePublish}
                onSchedule={() => {
                  void router.push('/schedule');
                }}
              />
            </section>
          )}

          {publishedProduct && (
            <p className="text-sm text-green-700">
              {t('generate.results.publishReady', {
                title: publishedProduct.title ?? t('generate.results.untitled'),
                price: formatCurrency(toPrice(publishedProduct.price) ?? 0, locale, listing?.currency ?? 'USD'),
              })}
            </p>
          )}

          {listing && (
            <section className="rounded border border-gray-200 bg-white p-4 shadow-sm">
              <h2 className="mb-2 text-lg font-semibold">{t('generate.results.listing')}</h2>
              {listing.title && <p className="font-medium">{listing.title}</p>}
              {listing.description && <p className="text-gray-700">{listing.description}</p>}
              {listing.listing_url && (
                <a className="text-blue-600 underline" href={listing.listing_url} target="_blank" rel="noreferrer">
                  {t('generate.results.viewListing')}
                </a>
              )}
            </section>
          )}

          {!hasContent && <p className="text-sm text-gray-600">{t('generate.results.noData')}</p>}
        </div>
      )}
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
