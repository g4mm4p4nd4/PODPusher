import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';

export default function Images() {
  const { t } = useTranslation('common');
  const [images, setImages] = useState<any[]>([]);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const ideaId = 1; // placeholder for demo

  const load = async () => {
    try {
      const res = await axios.get(`${api}/api/images`, { params: { idea_id: ideaId } });
      setImages(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const remove = async (id: number) => {
    await axios.delete(`${api}/api/images/${id}`);
    load();
  };

  const regenerate = async () => {
    await axios.post(`${api}/api/images/generate`, { idea_id: ideaId, style: 'default' });
    load();
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">{t('images.title')}</h1>
      <button onClick={regenerate} className="bg-blue-600 text-white px-4 py-2">
        {t('images.regenerate')}
      </button>
      <div className="grid grid-cols-2 gap-4">
        {images.map((img) => (
          <div key={img.id} className="border p-2">
            <img src={img.url} alt="" className="w-full" />
            <div className="flex justify-between mt-2">
              <button onClick={() => remove(img.id)} className="text-red-600">
                {t('images.delete')}
              </button>
              <button className="text-green-600">{t('images.select')}</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
