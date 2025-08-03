import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';
import Image from 'next/image';
import { generateSocialPost, SocialPost } from '../services/socialGenerator';

export default function SocialMediaGenerator() {
  const { t } = useTranslation('common');
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState<SocialPost | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const data = await generateSocialPost(prompt);
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('social.title')}</h1>
      <form onSubmit={submit} className="flex gap-2" aria-label={t('social.title')}>
        <label htmlFor="prompt" className="sr-only">
          {t('social.prompt')}
        </label>
        <input
          id="prompt"
          name="prompt"
          type="text"
          className="border p-2 flex-grow"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={t('social.prompt')}
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
          <p>{result.caption}</p>
          <Image
            src={result.image_url}
            alt={result.caption}
            width={256}
            height={256}
          />
        </div>
      )}
    </div>
  );
}
