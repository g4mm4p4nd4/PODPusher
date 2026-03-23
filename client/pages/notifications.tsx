import { getCommonStaticProps } from '../utils/translationProps';
import axios from 'axios';
import React, { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { getAuthHeaders, resolveApiUrl } from '../services/apiBase';

export type Notification = {
  id: number;
  message: string;
  type: string;
  created_at: string;
  read_status: boolean;
};

type NotificationUpdateState = {
  loading: boolean;
  error: string | null;
};

export default function Notifications() {
  const { t } = useTranslation('common');
  const [items, setItems] = useState<Notification[]>([]);
  const [meta, setMeta] = useState<NotificationUpdateState>({
    loading: false,
    error: null,
  });

  useEffect(() => {
    axios
      .get<Notification[]>(resolveApiUrl('/api/notifications'), { headers: getAuthHeaders() })
      .then((res) => setItems(res.data))
      .catch(() =>
        setMeta((currentMeta) => ({
          ...currentMeta,
          error: t('notifications.loadError'),
        }))
      );
  }, []);

  const markRead = async (id: number) => {
    setMeta({ loading: true, error: null });
    try {
      await axios.put(resolveApiUrl(`/api/notifications/${id}/read`), undefined, {
        headers: getAuthHeaders(),
      });
      setItems((currentItems) =>
        currentItems.map((n) => (n.id === id ? { ...n, read_status: true } : n))
      );
      setMeta({ loading: false, error: null });
    } catch {
      setMeta({
        loading: false,
        error: t('notifications.updateError'),
      });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{t('notifications.title')}</h1>
      {meta.error && <p role="alert">{meta.error}</p>}
      {meta.loading && <p>{t('notifications.processing')}</p>}
      <ul className="space-y-2">
        {items.map((n) => (
          <li
            key={n.id}
            className={`p-2 border rounded ${n.read_status ? 'opacity-50' : ''}`}
          >
            <div className="flex justify-between items-center">
              <span>[{n.type}] {n.message}</span>
              {!n.read_status && (
                <button
                  data-testid={`read-${n.id}`}
                  disabled={meta.loading}
                  onClick={() => markRead(n.id)}
                  className="text-sm text-blue-500"
                >
                  {t('notifications.markRead')}
                </button>
              )}
            </div>
            <div className="text-xs text-gray-500">
              {new Date(n.created_at).toLocaleString()}
            </div>
          </li>
        ))}
      </ul>
      {items.length === 0 && <p>{t('notifications.empty')}</p>}
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
