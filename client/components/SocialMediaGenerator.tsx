import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { generateSocialPost, SocialPost, SocialRequest } from '../services/socialGenerator';

export default function SocialMediaGenerator() {
  const { t } = useTranslation('common');
  const [form, setForm] = useState<SocialRequest>({ language: 'en' });
  const [result, setResult] = useState<SocialPost | null>(null);
  const [loading, setLoading] = useState(false);

  const update = (field: keyof SocialRequest, value: any) => {
    setForm({ ...form, [field]: value });
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const data = await generateSocialPost(form);
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const copyCaption = () => {
    if (result) navigator.clipboard.writeText(result.caption);
  };

  const downloadImage = () => {
    if (!result?.image) return;
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${result.image}`;
    link.download = 'social.png';
    link.click();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('social.title')}</h1>
      <form onSubmit={submit} className="space-y-2" aria-label={t('social.title')}>
        <input
          id="title"
          className="border p-2 w-full"
          value={form.title || ''}
          onChange={(e) => update('title', e.target.value)}
          placeholder={t('social.titleField')}
        />
        <textarea
          id="description"
          className="border p-2 w-full"
          value={form.description || ''}
          onChange={(e) => update('description', e.target.value)}
          placeholder={t('social.descriptionField')}
        />
        <input
          id="tags"
          className="border p-2 w-full"
          value={form.tags?.join(',') || ''}
          onChange={(e) => update('tags', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
          placeholder={t('social.tagsField')}
        />
        <input
          id="product_type"
          className="border p-2 w-full"
          value={form.product_type || ''}
          onChange={(e) => update('product_type', e.target.value)}
          placeholder={t('social.typeField')}
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2"
        >
          {loading ? '...' : t('social.button')}
        </button>
      </form>
      {result && (
        <div className="space-y-4">
          <textarea
            className="border p-2 w-full"
            value={result.caption}
            onChange={(e) => setResult({ ...result, caption: e.target.value })}
          />
          {result.image && (
            <img
              src={`data:image/png;base64,${result.image}`}
              alt={result.caption}
              className="w-64 h-64 object-contain"
            />
          )}
          <div className="flex gap-2">
            <button type="button" className="px-4 py-2 bg-gray-200" onClick={copyCaption}>
              {t('social.copy')}
            </button>
            {result.image && (
              <button type="button" className="px-4 py-2 bg-gray-200" onClick={downloadImage}>
                {t('social.download')}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
