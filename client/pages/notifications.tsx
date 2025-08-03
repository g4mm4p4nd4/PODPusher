import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';

export type Notification = {
  id: number;
  message: string;
  type: string;
  created_at: string;
  read_status: boolean;
};

export default function Notifications() {
  const { t } = useTranslation('common');
  const [items, setItems] = useState<Notification[]>([]);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    axios
      .get<Notification[]>(`${api}/api/notifications`, {
        headers: { 'X-User-Id': '1' },
      })
      .then(res => setItems(res.data))
      .catch(err => console.error(err));
  }, [api]);

  const markRead = async (id: number) => {
    await axios.put(`${api}/api/notifications/${id}/read`);
    setItems(items.map(n => (n.id === id ? { ...n, read_status: true } : n)));
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{t('notifications.title')}</h1>
      <ul className="space-y-2">
        {items.map(n => (
          <li
            key={n.id}
            className={`p-2 border rounded ${n.read_status ? 'opacity-50' : ''}`}
          >
            <div className="flex justify-between items-center">
              <span>[{n.type}] {n.message}</span>
              {!n.read_status && (
                <button
                  data-testid={`read-${n.id}`}
                  onClick={() => markRead(n.id)}
                  className="text-sm text-blue-500"
                >
                  {t('notifications.markRead')}
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
