import axios from 'axios';
import { useState } from 'react';
import { useTranslation } from 'next-i18next';

export default function Schedule() {
  const { t } = useTranslation('common');
  const [form, setForm] = useState({
    type: 'scheduled_post',
    message: '',
    delivery_method: 'in_app',
    scheduled_at: '',
  });
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await axios.post(
      `${api}/api/notifications/schedule`,
      {
        ...form,
        scheduled_at: form.scheduled_at
          ? new Date(form.scheduled_at).toISOString()
          : null,
      },
      { headers: { 'X-User-Id': '1' } }
    );
    setForm({ type: 'scheduled_post', message: '', delivery_method: 'in_app', scheduled_at: '' });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{t('schedule.title')}</h1>
      <form onSubmit={submit} className="space-y-4 max-w-md">
        <div>
          <label className="block mb-1">{t('schedule.message')}</label>
          <input
            value={form.message}
            onChange={(e) => setForm({ ...form, message: e.target.value })}
            className="border p-2 w-full"
          />
        </div>
        <div>
          <label className="block mb-1">{t('schedule.type')}</label>
          <select
            value={form.type}
            onChange={(e) => setForm({ ...form, type: e.target.value })}
            className="border p-2 w-full"
          >
            <option value="scheduled_post">{t('schedule.types.scheduled_post')}</option>
            <option value="quota_reset">{t('schedule.types.quota_reset')}</option>
            <option value="trending_product">{t('schedule.types.trending_product')}</option>
          </select>
        </div>
        <div>
          <label className="block mb-1">{t('schedule.delivery')}</label>
          <select
            value={form.delivery_method}
            onChange={(e) => setForm({ ...form, delivery_method: e.target.value })}
            className="border p-2 w-full"
          >
            <option value="in_app">{t('schedule.deliveryMethods.in_app')}</option>
            <option value="email">{t('schedule.deliveryMethods.email')}</option>
            <option value="push">{t('schedule.deliveryMethods.push')}</option>
          </select>
        </div>
        <div>
          <label className="block mb-1">{t('schedule.when')}</label>
          <input
            type="datetime-local"
            value={form.scheduled_at}
            onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
            className="border p-2 w-full"
          />
        </div>
        <button type="submit" className="bg-blue-500 text-white px-4 py-2">
          {t('schedule.submit')}
        </button>
      </form>
    </div>
  );
}
