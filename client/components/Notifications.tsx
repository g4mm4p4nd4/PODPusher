import { useEffect, useState } from 'react';
import axios from 'axios';

export interface Notification {
  id: number;
  message: string;
  read: boolean;
}

export default function Notifications() {
  const [items, setItems] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const fetchItems = () => {
    axios
      .get<Notification[]>(`${api}/api/notifications`, { headers: { 'X-User-Id': '1' } })
      .then(res => setItems(res.data))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const markRead = async (id: number) => {
    await axios.put(`${api}/api/notifications/${id}/read`);
    fetchItems();
  };

  return (
    <div className="relative" data-testid="notifications">
      <button onClick={() => setOpen(!open)} className="relative">
        <span>🔔</span>
        {items.some(i => !i.read) && (
          <span className="absolute -top-1 -right-1 bg-red-500 rounded-full w-2 h-2" />
        )}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-64 bg-white border shadow-lg z-10">
          <ul className="p-2 space-y-1 text-sm">
            {items.map(n => (
              <li key={n.id} className="flex justify-between gap-2">
                <span className={n.read ? 'text-gray-500' : ''}>{n.message}</span>
                {!n.read && (
                  <button onClick={() => markRead(n.id)} className="text-blue-600 text-xs">
                    Mark read
                  </button>
                )}
              </li>
            ))}
            {items.length === 0 && <li>No notifications</li>}
          </ul>
        </div>
      )}
    </div>
  );
}
