import axios from 'axios';
import { useState } from 'react';
import { useTranslation } from 'next-i18next';

export default function ListingComposer() {
  const { t } = useTranslation('common');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [loading, setLoading] = useState(false);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const suggestTags = async () => {
    setLoading(true);
    try {
      const res = await axios.post<string[]>(`${api}/suggest-tags`, {
        description,
      });
      setTags(res.data.join(', '));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium">
          {t('listings.titleLabel')} ({title.length}/140 {t('listings.characters')})
        </label>
        <input
          data-testid="title-input"
          type="text"
          className="border p-2 w-full"
          value={title}
          onChange={e => setTitle(e.target.value)}
        />
      </div>
      <div>
        <label className="block text-sm font-medium">
          {t('listings.descriptionLabel')} ({description.length}/2000 {t('listings.characters')})
        </label>
        <textarea
          data-testid="description-input"
          className="border p-2 w-full"
          value={description}
          onChange={e => setDescription(e.target.value)}
        />
      </div>
      <div>
        <label className="block text-sm font-medium" htmlFor="tags">
          {t('listings.tagsLabel')}
        </label>
        <input
          id="tags"
          data-testid="tags-input"
          type="text"
          className="border p-2 w-full"
          value={tags}
          onChange={e => setTags(e.target.value)}
        />
        <button
          type="button"
          data-testid="suggest-button"
          onClick={suggestTags}
          className="mt-2 bg-blue-600 text-white px-4 py-1"
        >
          {loading ? '...' : t('listings.suggest')}
        </button>
      </div>
    </div>
  );
}
