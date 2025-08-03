import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';
import { fetchTagSuggestions } from '../services/listings';

interface Props {
  onPublish?: (data: any) => void;
}

export default function ListingComposer({ onPublish }: Props) {
  const { t } = useTranslation('common');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [suggested, setSuggested] = useState<string[]>([]);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const getSuggestions = async () => {
    try {
      const res = await fetchTagSuggestions(title, description);
      setSuggested(res);
    } catch (err) {
      console.error(err);
    }
  };

  const toggleTag = (tag: string) => {
    if (tags.includes(tag)) {
      setTags(tags.filter(t => t !== tag));
    } else if (tags.length < 13) {
      setTags([...tags, tag]);
    }
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onPublish?.({ title, description, tags });
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <div>
        <label htmlFor="title" className="block text-sm font-medium mb-1">
          {t('listings.title')} ({title.length}/140)
        </label>
        <input
          id="title"
          className="border p-2 w-full"
          maxLength={140}
          value={title}
          onChange={e => setTitle(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="description" className="block text-sm font-medium mb-1">
          {t('listings.description')} ({description.length}/1000)
        </label>
        <textarea
          id="description"
          className="border p-2 w-full"
          maxLength={1000}
          rows={4}
          value={description}
          onChange={e => setDescription(e.target.value)}
        />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1">
          {t('listings.tags')} ({tags.length}/13)
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {tags.map(tg => (
            <span
              key={tg}
              className="bg-gray-200 px-2 py-1 rounded cursor-pointer"
              onClick={() => toggleTag(tg)}
            >
              {tg}
            </span>
          ))}
        </div>
        <button
          type="button"
          onClick={getSuggestions}
          className="text-sm text-blue-500"
        >
          {t('listings.suggest')}
        </button>
        <div className="flex flex-wrap gap-2 mt-2">
          {suggested.map(tag => (
            <button
              type="button"
              key={tag}
              onClick={() => toggleTag(tag)}
              className={`border px-2 py-1 rounded ${tags.includes(tag) ? 'bg-blue-600 text-white' : ''}`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>
      <button type="submit" className="bg-blue-600 text-white px-4 py-2">
        {t('listings.publish')}
      </button>
    </form>
  );
}
