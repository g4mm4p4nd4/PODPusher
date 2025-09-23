import React, { useCallback, useMemo, useState } from 'react';

export interface ReviewProduct {
  id: number;
  name: string;
  image_url: string;
  rating?: number | null;
  tags?: string[] | null;
  flagged?: boolean | null;
}

interface ImageCardProps {
  product: ReviewProduct;
  onOptimisticUpdate: (id: number, changes: Partial<ReviewProduct>) => void;
  onCommit: (id: number, changes: Partial<ReviewProduct>) => Promise<void>;
  onRollback: (id: number, previous: ReviewProduct) => void;
  onError?: (id: number, error: unknown) => void;
  errorMessage?: string | null;
  isPending?: boolean;
}

const STAR_VALUES = [1, 2, 3, 4, 5];

const ImageCard: React.FC<ImageCardProps> = ({
  product,
  onOptimisticUpdate,
  onCommit,
  onRollback,
  onError,
  errorMessage,
  isPending = false,
}) => {
  const [pending, setPending] = useState(false);
  const [tagInput, setTagInput] = useState('');

  const effectivePending = pending || isPending;

  const currentTags = useMemo(() => product.tags ?? [], [product.tags]);

  const applyChange = useCallback(
    async (changes: Partial<ReviewProduct>): Promise<boolean> => {
      if (effectivePending) {
        return false;
      }

      const previous: ReviewProduct = {
        ...product,
        tags: product.tags ? [...product.tags] : [],
      };

      setPending(true);
      onOptimisticUpdate(product.id, changes);

      try {
        await onCommit(product.id, changes);
        return true;
      } catch (error) {
        onRollback(product.id, previous);
        onError?.(product.id, error);
        return false;
      } finally {
        setPending(false);
      }
    },
    [effectivePending, onCommit, onError, onOptimisticUpdate, onRollback, product]
  );

  const handleStarClick = useCallback(
    async (value: number) => {
      await applyChange({ rating: value });
    },
    [applyChange]
  );

  const handleClearRating = useCallback(async () => {
    await applyChange({ rating: null });
  }, [applyChange]);

  const handleToggleFlag = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      await applyChange({ flagged: event.target.checked });
    },
    [applyChange]
  );

  const addTag = useCallback(
    async (tagValue: string) => {
      const newTags = tagValue
        .split(',')
        .map(tag => tag.trim())
        .filter(Boolean);

      if (newTags.length === 0) {
        return;
      }

      const uniqueTags = Array.from(new Set([...currentTags, ...newTags]));
      const success = await applyChange({ tags: uniqueTags });
      if (success) {
        setTagInput('');
      }
    },
    [applyChange, currentTags]
  );

  const removeTag = useCallback(
    async (tag: string) => {
      const filtered = currentTags.filter(existing => existing !== tag);
      await applyChange({ tags: filtered });
    },
    [applyChange, currentTags]
  );

  const handleTagSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      await addTag(tagInput);
    },
    [addTag, tagInput]
  );

  const handleInputKeyDown = useCallback(
    async (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        await addTag(tagInput);
      }
    },
    [addTag, tagInput]
  );

  return (
    <div className="border p-4 rounded space-y-4" data-testid={`image-card-${product.id}`}>
      <div className="space-y-2">
        <img src={product.image_url} alt={product.name} className="w-full h-auto rounded" />
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{product.name}</h2>
          <button
            type="button"
            onClick={handleClearRating}
            className="text-sm text-blue-600 hover:underline disabled:text-gray-400"
            disabled={effectivePending || product.rating == null}
          >
            Clear
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2" role="group" aria-label="rating">
        {STAR_VALUES.map(value => {
          const active = (product.rating ?? 0) >= value;
          return (
            <button
              key={value}
              type="button"
              className={`text-2xl ${active ? 'text-yellow-400' : 'text-gray-300'} disabled:text-gray-200`}
              aria-label={`Set rating to ${value}`}
              aria-pressed={active}
              data-testid={`star-${product.id}-${value}`}
              onClick={() => handleStarClick(value)}
              disabled={effectivePending}
            >
              ★
            </button>
          );
        })}
      </div>

      <div className="space-y-2">
        <div className="flex flex-wrap gap-2" aria-label="tags">
          {currentTags.map(tag => (
            <span
              key={tag}
              className="inline-flex items-center bg-gray-100 rounded-full px-3 py-1 text-sm"
            >
              <span>{tag}</span>
              <button
                type="button"
                className="ml-2 text-xs text-red-500 hover:underline disabled:text-gray-300"
                onClick={() => removeTag(tag)}
                disabled={effectivePending}
                aria-label={`Remove tag ${tag}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <form className="flex gap-2" onSubmit={handleTagSubmit}>
          <input
            type="text"
            value={tagInput}
            onChange={event => setTagInput(event.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Add tag"
            className="flex-1 border rounded px-3 py-2"
            disabled={effectivePending}
            aria-label="Add tag input"
          />
          <button
            type="submit"
            className="px-3 py-2 bg-blue-600 text-white rounded disabled:bg-gray-300"
            disabled={effectivePending}
          >
            Add
          </button>
        </form>
      </div>

      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={product.flagged ?? false}
          onChange={handleToggleFlag}
          disabled={effectivePending}
          data-testid={`flag-toggle-${product.id}`}
        />
        <span className="text-sm">Flag for review</span>
      </label>

      {errorMessage ? (
        <p className="text-sm text-red-600" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
};

export default ImageCard;
