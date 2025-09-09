import axios from 'axios';
import { useState } from 'react';
import { useTranslation } from 'next-i18next';

export default function Images() {
  const { t } = useTranslation('common');
  const [ideaId, setIdeaId] = useState('');
  const [style, setStyle] = useState('');
  const [provider, setProvider] = useState('');
  const [images, setImages] = useState<string[]>([]);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const generate = async () => {
    try {
      const res = await axios.post<{ urls: string[] }>(`${api}/api/images/generate`, {
        idea_id: Number(ideaId),
        style,
        provider_override: provider || undefined,
      });
      setImages(res.data.urls);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('images.title')}</h1>
      <div className="flex flex-wrap gap-2 items-end">
        <div>
          <label className="block text-sm font-medium">{t('images.ideaId')}</label>
          <input
            name="ideaId"
            value={ideaId}
            onChange={e => setIdeaId(e.target.value)}
            className="border p-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">{t('images.style')}</label>
          <input
            name="style"
            value={style}
            onChange={e => setStyle(e.target.value)}
            className="border p-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">{t('images.provider')}</label>
          <select
            value={provider}
            onChange={e => setProvider(e.target.value)}
            className="border p-2"
          >
            <option value="">{t('images.default')}</option>
            <option value="openai">OpenAI</option>
            <option value="gemini">Gemini</option>
          </select>
        </div>
        <button onClick={generate} className="bg-blue-600 text-white px-4 py-2">
          {t('images.generate')}
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {images.map((url, idx) => (
          <div key={idx} className="space-y-2">
            <img src={url} alt={`generated-${idx}`} className="w-full h-auto" />
            <div className="flex gap-2">
              <button
                onClick={() => setImages(imgs => imgs.filter((_, i) => i !== idx))}
                className="bg-red-500 text-white px-2 py-1 text-sm"
              >
                {t('images.delete')}
              </button>
              <button onClick={generate} className="bg-gray-500 text-white px-2 py-1 text-sm">
                {t('images.regenerate')}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
