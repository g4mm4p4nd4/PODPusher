import axios from 'axios';
import { useState } from 'react';

export default function ListingComposer() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);

  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const titleLimit = 140;
  const descLimit = 1000;

  const fetchTags = async () => {
    try {
      const res = await axios.post(`${api}/suggest-tags`, { description });
      setTags(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block font-medium">
          Title
          <span className="ml-2 text-sm text-gray-500" data-testid="title-count">
            {title.length}/{titleLimit}
          </span>
        </label>
        <input
          type="text"
          className="border p-2 w-full"
          value={title}
          onChange={e => setTitle(e.target.value.slice(0, titleLimit))}
        />
      </div>
      <div>
        <label className="block font-medium">
          Description
          <span className="ml-2 text-sm text-gray-500" data-testid="desc-count">
            {description.length}/{descLimit}
          </span>
        </label>
        <textarea
          className="border p-2 w-full"
          rows={4}
          value={description}
          onChange={e => setDescription(e.target.value.slice(0, descLimit))}
        />
      </div>
      <button
        type="button"
        className="bg-blue-600 text-white px-4 py-2"
        onClick={fetchTags}
        data-testid="suggest-btn"
      >
        Get Tag Suggestions
      </button>
      {tags.length > 0 && (
        <ul className="flex flex-wrap gap-2 mt-2" data-testid="tag-list">
          {tags.map(t => (
            <li key={t} className="bg-gray-200 px-2 py-1 rounded">
              {t}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
