import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';

interface Img {
  id: number | null;
  url: string;
  provider?: string;
}

export default function ImagesPage() {
  const { t } = useTranslation('common');
  const [ideaId, setIdeaId] = useState('');
  const [style, setStyle] = useState('');
  const [images, setImages] = useState<Img[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    if (ideaId) {
      axios
        .get<Img[]>(`${api}/api/images/${ideaId}`)
        .then((res) => setImages(res.data))
        .catch(() => {});
    }
  }, [api, ideaId]);

  const generate = async () => {
    try {
      const res = await axios.post<Img[]>(`${api}/api/images/generate`, {
        idea_id: Number(ideaId),
        style,
      });
      setImages(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const remove = async (id: number) => {
    try {
      await axios.delete(`${api}/api/images/${id}`);
      setImages((imgs) => imgs.filter((i) => i.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{t('images.title')}</h1>
      <div className="flex gap-2">
        <input
          className="border p-2"
          placeholder={t('images.ideaId')}
          value={ideaId}
          onChange={(e) => setIdeaId(e.target.value)}
        />
        <input
          className="border p-2"
          placeholder={t('images.style')}
          value={style}
          onChange={(e) => setStyle(e.target.value)}
        />
        <button
          type="button"
          onClick={generate}
          className="bg-blue-600 text-white px-4 py-2"
        >
          {t('images.generate')}
        </button>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {images.map((img) => (
          <div
            key={img.id ?? img.url}
            className={`border p-2 space-y-2 ${
              selected === img.id ? 'ring-2 ring-blue-500' : ''
            }`}
          >
            <img src={img.url} alt="generated" className="w-full h-auto" />
            <div className="flex gap-2 text-sm">
              <button
                type="button"
                onClick={() => setSelected(img.id ?? 0)}
                className="text-blue-600"
              >
                {t('images.select')}
              </button>
              {img.id && (
                <button
                  type="button"
                  onClick={() => remove(img.id!)}
                  className="text-red-600"
                >
                  {t('images.delete')}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
