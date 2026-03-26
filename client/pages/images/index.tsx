import axios from 'axios';
import React, { ChangeEvent, useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';

import { getApiBase, getAuthHeaders } from '../../services/apiBase';

type GeneratedImage = {
  id: number;
  idea_id: number;
  image_url?: string;
  url?: string;
  provider?: string;
  generation_source?: string;
};

const DEFAULT_IDEA_ID = 1;
const DEFAULT_STYLE = 'default';
const DEFAULT_PROVIDER = 'default';

export default function Images() {
  const { t } = useTranslation('common');
  const [images, setImages] = useState<GeneratedImage[]>([]);
  const [ideaId, setIdeaId] = useState(DEFAULT_IDEA_ID);
  const [style, setStyle] = useState(DEFAULT_STYLE);
  const [provider, setProvider] = useState(DEFAULT_PROVIDER);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const api = getApiBase();

  const load = async (nextIdeaId: number = ideaId) => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${api}/api/images`, {
        params: { idea_id: nextIdeaId },
        headers: getAuthHeaders(),
      });
      setImages(res.data);
      if (!res.data.some((image: GeneratedImage) => image.id === selectedId)) {
        setSelectedId(null);
      }
    } catch (err) {
      console.error(err);
      setError(t('images.error'));
      setImages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [ideaId]);

  const handleIdeaIdChange = (event: ChangeEvent<HTMLInputElement>) => {
    const parsed = Number(event.target.value);
    setIdeaId(Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_IDEA_ID);
  };

  const regenerate = async () => {
    setLoading(true);
    setError('');
    try {
      await axios.post(
        `${api}/api/images/generate`,
        {
          idea_id: ideaId,
          style,
          provider_override: provider === DEFAULT_PROVIDER ? undefined : provider,
        },
        { headers: getAuthHeaders() },
      );
      await load();
    } catch (err) {
      console.error(err);
      setError(t('images.error'));
      setLoading(false);
    }
  };

  const remove = async (id: number) => {
    setLoading(true);
    setError('');
    try {
      await axios.delete(`${api}/api/images/${id}`, { headers: getAuthHeaders() });
      await load();
    } catch (err) {
      console.error(err);
      setError(t('images.error'));
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-end">
        <div className="flex flex-col gap-1">
          <label htmlFor="idea-id" className="font-medium">{t('images.ideaId')}</label>
          <input
            id="idea-id"
            type="number"
            min={1}
            value={ideaId}
            onChange={handleIdeaIdChange}
            className="rounded border px-3 py-2"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="image-style" className="font-medium">{t('images.style')}</label>
          <input
            id="image-style"
            value={style}
            onChange={(event) => setStyle(event.target.value)}
            className="rounded border px-3 py-2"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="image-provider" className="font-medium">{t('images.provider')}</label>
          <select
            id="image-provider"
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
            className="rounded border px-3 py-2"
          >
            <option value="default">{t('images.providers.default')}</option>
            <option value="openai">{t('images.providers.openai')}</option>
            <option value="stub">{t('images.providers.stub')}</option>
          </select>
        </div>
        <button
          type="button"
          onClick={regenerate}
          className="rounded bg-blue-600 px-4 py-2 text-white"
          disabled={loading}
        >
          {t('images.regenerate')}
        </button>
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold">{t('images.title')}</h1>
        {error ? <p className="text-red-600">{error}</p> : null}
        {loading ? <p>{t('images.loading')}</p> : null}
      </div>

      {!loading && images.length === 0 ? (
        <p>{t('images.empty')}</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {images.map((image) => {
            const url = image.url || image.image_url || '';
            const source = image.provider || image.generation_source || t('images.providers.default');
            const isSelected = selectedId === image.id;

            return (
              <div key={image.id} className="space-y-2 rounded border p-3">
                <img src={url} alt={`Generated image ${image.id}`} className="w-full rounded" />
                <p className="text-sm text-gray-600">
                  {t('images.source')}: {source}
                </p>
                <div className="flex gap-3">
                  <button type="button" onClick={() => remove(image.id)} className="text-red-600">
                    {t('images.delete')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedId(image.id)}
                    className="text-green-600"
                  >
                    {isSelected ? t('images.selected') : t('images.select')}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
