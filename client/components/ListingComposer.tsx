import React, { useState, useEffect } from 'react';
import { useTranslation } from 'next-i18next';
import {
  fetchTagSuggestions,
  saveDraft,
  loadDraft,
  DraftData,
} from '../services/listings';

interface Props {
  onPublish?: (data: any) => void;
}

export default function ListingComposer({ onPublish }: Props) {
  const { t } = useTranslation('common');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [suggested, setSuggested] = useState<string[]>([]);
  const [language, setLanguage] = useState('en');
  const [fieldOrder, setFieldOrder] = useState<string[]>([
    'title',
    'description',
    'tags',
  ]);
  const [dragIndex, setDragIndex] = useState<number | null>(null);

  useEffect(() => {
    const id = localStorage.getItem('draftId');
    if (id) {
      loadDraft(Number(id))
        .then((d: DraftData) => {
          setTitle(d.title);
          setDescription(d.description);
          setTags(d.tags);
          setLanguage(d.language);
          if (d.field_order.length) setFieldOrder(d.field_order);
        })
        .catch(() => {});
    }
  }, []);

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

  const save = async () => {
    try {
      const id = await saveDraft({
        id: Number(localStorage.getItem('draftId')) || undefined,
        title,
        description,
        tags,
        language,
        field_order: fieldOrder,
      });
      localStorage.setItem('draftId', String(id));
    } catch (err) {
      console.error(err);
    }
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onPublish?.({ title, description, tags, language, field_order: fieldOrder });
  };

  const handleDragStart = (index: number) => setDragIndex(index);
  const handleDrop = (index: number) => {
    if (dragIndex === null) return;
    const order = [...fieldOrder];
    const [moved] = order.splice(dragIndex, 1);
    order.splice(index, 0, moved);
    setFieldOrder(order);
    setDragIndex(null);
  };

  const renderField = (field: string) => {
    switch (field) {
      case 'title':
        return (
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
        );
      case 'description':
        return (
          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium mb-1"
            >
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
        );
      case 'tags':
        return (
          <div>
            <label className="block text-sm font-medium mb-1">
              {t('listings.tags')} ({tags.length}/13)
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {tags.map((tg, i) => (
                <span
                  key={tg}
                  className="bg-gray-200 px-2 py-1 rounded cursor-pointer"
                  draggable
                  onDragStart={() => handleDragStart(i)}
                  onDrop={() => handleDrop(i)}
                  onDragOver={e => e.preventDefault()}
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
                  className={`border px-2 py-1 rounded ${
                    tags.includes(tag) ? 'bg-blue-600 text-white' : ''
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">
          {t('listings.language')}
        </label>
        <select
          value={language}
          onChange={e => setLanguage(e.target.value)}
          className="border p-2"
        >
          <option value="en">{t('languages.en')}</option>
          <option value="es">{t('languages.es')}</option>
        </select>
      </div>
      {fieldOrder.map((field, idx) => (
        <div
          key={field}
          draggable
          onDragStart={() => handleDragStart(idx)}
          onDragOver={e => e.preventDefault()}
          onDrop={() => handleDrop(idx)}
          className="p-2 border rounded"
        >
          {renderField(field)}
        </div>
      ))}
      <div className="flex gap-2">
        <button type="submit" className="bg-blue-600 text-white px-4 py-2">
          {t('listings.publish')}
        </button>
        <button
          type="button"
          onClick={save}
          className="bg-gray-200 px-4 py-2"
        >
          {t('listings.save')}
        </button>
      </div>
    </form>
  );
}
