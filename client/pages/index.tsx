import axios from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { resolveApiUrl } from '../services/apiBase';

type Trend = { term: string; category: string };

type TrendsByCategory = Record<string, string[]>;

export default function Home() {
  const { t } = useTranslation('common');
  const [trends, setTrends] = useState<TrendsByCategory>({});
  const [events, setEvents] = useState<string[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get<Trend[]>(resolveApiUrl('/trends'));
        const grouped: TrendsByCategory = {};
        res.data.forEach(t => {
          if (!grouped[t.category]) grouped[t.category] = [];
          grouped[t.category].push(t.term);
        });
        setTrends(grouped);
        const month = new Date().toLocaleString('default', { month: 'long' }).toLowerCase();
        const ev = await axios.get<{ month: string; events: string[] }>(resolveApiUrl(`/events/${month}`));
        setEvents(ev.data.events);
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('index.trending')}</h1>
      {Object.entries(trends).map(([cat, terms]) => (
        <div key={cat}>
          <h2 className="text-xl font-semibold capitalize">{cat}</h2>
          <ul className="list-disc list-inside pl-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1">
            {terms.map(term => (
              <li key={term}>{term}</li>
            ))}
          </ul>
        </div>
      ))}
      <div>
        <h2 className="text-xl font-semibold mt-4">{t('index.events')}</h2>
        <ul className="list-disc list-inside pl-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1">
          {events.map(ev => (
            <li key={ev}>{ev}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
