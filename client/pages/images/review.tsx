import axios, { isAxiosError } from 'axios';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'next-i18next';
import ImageCard, { ReviewProduct } from '../../components/ImageCard';

interface ReviewResponse {
  items?: ReviewProduct[];
  nextPage?: number | null;
  hasMore?: boolean;
}

type ProductErrorMap = Record<number, string | undefined>;
type ProductPendingMap = Record<number, boolean | undefined>;

const mergeProducts = (existing: ReviewProduct[], incoming: ReviewProduct[]): ReviewProduct[] => {
  const map = new Map<number, ReviewProduct>();
  existing.forEach(item => map.set(item.id, item));
  incoming.forEach(item => map.set(item.id, item));
  return Array.from(map.values());
};

const parseResponse = (
  data: ReviewResponse | ReviewProduct[] | undefined,
  currentPage: number
): { items: ReviewProduct[]; nextPage: number | null; hasMore: boolean } => {
  if (!data) {
    return { items: [], nextPage: null, hasMore: false };
  }

  if (Array.isArray(data)) {
    const hasItems = data.length > 0;
    return {
      items: data,
      nextPage: hasItems ? currentPage + 1 : null,
      hasMore: hasItems,
    };
  }

  const items = data.items ?? [];
  const explicitNext = typeof data.nextPage === 'number' ? data.nextPage : null;
  const hasMore = typeof data.hasMore === 'boolean' ? data.hasMore : explicitNext !== null;

  return {
    items,
    nextPage: explicitNext ?? (hasMore && items.length > 0 ? currentPage + 1 : null),
    hasMore: hasMore && items.length > 0,
  };
};

const ImageReview = () => {
  const { t } = useTranslation('common');
  const apiBase = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    []
  );

  const [products, setProducts] = useState<ReviewProduct[]>([]);
  const [errorMap, setErrorMap] = useState<ProductErrorMap>({});
  const [pendingMap, setPendingMap] = useState<ProductPendingMap>({});
  const [pageCursor, setPageCursor] = useState<number | null>(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const observerRef = useRef<IntersectionObserver | null>(null);

  const loadPage = useCallback(async () => {
    if (loading || pageCursor === null) {
      return;
    }

    setLoading(true);
    const pageToLoad = pageCursor;

    try {
      const response = await axios.get<ReviewResponse | ReviewProduct[]>(
        `${apiBase}/api/products/review`,
        {
          params: { page: pageToLoad },
        }
      );

      const parsed = parseResponse(response.data, pageToLoad);
      setProducts(prev => mergeProducts(prev, parsed.items));
      setPageCursor(parsed.nextPage);
      setHasMore(parsed.hasMore);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [apiBase, loading, pageCursor]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  const sentinelRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }

      if (!node) {
        return;
      }

      observerRef.current = new IntersectionObserver(entries => {
        const firstEntry = entries[0];
        if (firstEntry?.isIntersecting && hasMore) {
          loadPage();
        }
      });

      observerRef.current.observe(node);
    },
    [hasMore, loadPage]
  );

  useEffect(() => {
    return () => observerRef.current?.disconnect();
  }, []);

  const handleOptimisticUpdate = useCallback(
    (id: number, changes: Partial<ReviewProduct>) => {
      setProducts(prev =>
        prev.map(product => (product.id === id ? { ...product, ...changes } : product))
      );
      setErrorMap(prev => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    },
    []
  );

  const handleCommit = useCallback(
    async (id: number, changes: Partial<ReviewProduct>) => {
      setPendingMap(prev => ({ ...prev, [id]: true }));
      try {
        await axios.put(`${apiBase}/api/products/review/${id}`, changes);
      } catch (error) {
        throw error;
      } finally {
        setPendingMap(prev => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
      }
    },
    [apiBase]
  );

  const handleRollback = useCallback((id: number, previous: ReviewProduct) => {
    setProducts(prev => prev.map(product => (product.id === id ? previous : product)));
  }, []);

  const handleError = useCallback(
    (id: number, error: unknown) => {
      const fallback = t('review.updateError', {
        defaultValue: 'Unable to update. Please try again.',
      });

      const message = isAxiosError(error)
        ? error.response?.data?.detail || fallback
        : fallback;

      setErrorMap(prev => ({ ...prev, [id]: message }));
    },
    [t]
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('review.title')}</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {products.map(product => (
          <ImageCard
            key={product.id}
            product={product}
            onOptimisticUpdate={handleOptimisticUpdate}
            onCommit={handleCommit}
            onRollback={handleRollback}
            onError={handleError}
            errorMessage={errorMap[product.id]}
            isPending={Boolean(pendingMap[product.id])}
          />
        ))}
      </div>
      {products.length === 0 && !loading ? (
        <p>{t('review.noProducts')}</p>
      ) : null}
      <div ref={sentinelRef} />
      {loading ? <p>{t('review.loading', { defaultValue: 'Loading…' })}</p> : null}
    </div>
  );
};

export default ImageReview;
