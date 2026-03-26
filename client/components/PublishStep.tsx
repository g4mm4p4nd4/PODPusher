import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';

interface Props {
  product: {
    image_url?: string;
  };
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
      .map((tag) => tag.trim())
      .filter(Boolean);

    onPublish({ price, tags: tagList });
  };

  return (
    <div>
      <div className="flex gap-2">
        {product.image_url && <img src={product.image_url} alt="mockup" className="h-24 w-24" />}
      </div>
      <div className="mt-2">
        <label>{t('publish.price')}</label>
        <input
          type="number"
          value={price}
          onChange={(e) => setPrice(Number(e.target.value))}
          className="ml-2 border p-1"
        />
      </div>
      <div className="mt-2">
        <label>{t('publish.tags')}</label>
        <input
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          className="ml-2 border p-1"
        />
      </div>
      <div className="mt-4 flex gap-2">
        <button type="button" onClick={submit} className="bg-blue-600 px-4 py-2 text-white">
          {t('publish.publishNow')}
        </button>
        {onSchedule && (
          <button type="button" onClick={onSchedule} className="bg-gray-200 px-4 py-2">
            {t('publish.schedule')}
          </button>
        )}
      </div>
    </div>
  );
}
