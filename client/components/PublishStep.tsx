import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';

interface Props {
  product: { mockups: string[] };
  onPublish: (data: { price: number; tags: string[] }) => void;
  onSchedule?: () => void;
}

export default function PublishStep({ product, onPublish, onSchedule }: Props) {
  const { t } = useTranslation('common');
  const [price, setPrice] = useState(0);
  const [tags, setTags] = useState('');

  const submit = () => {
    const tagList = tags
      .split(',')
      .map(t => t.trim())
      .filter(Boolean);
    onPublish({ price, tags: tagList });
  };

  return (
    <div>
      <div className="flex gap-2">
        {product.mockups.map(src => (
          <img key={src} src={src} alt="mockup" className="w-24 h-24" />
        ))}
      </div>
      <div className="mt-2">
        <label>{t('publish.price')}</label>
        <input
          type="number"
          value={price}
          onChange={e => setPrice(Number(e.target.value))}
          className="border ml-2 p-1"
        />
      </div>
      <div className="mt-2">
        <label>{t('publish.tags')}</label>
        <input
          value={tags}
          onChange={e => setTags(e.target.value)}
          className="border ml-2 p-1"
        />
      </div>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={submit}
          className="bg-blue-600 text-white px-4 py-2"
        >
          {t('publish.publishNow')}
        </button>
        {onSchedule && (
          <button
            type="button"
            onClick={onSchedule}
            className="bg-gray-200 px-4 py-2"
          >
            {t('publish.schedule')}
          </button>
        )}
      </div>
    </div>
  );
}
