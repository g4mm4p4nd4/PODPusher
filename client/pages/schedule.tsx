import axios from 'axios';
import React, { FormEvent, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { getAuthHeaders, resolveApiUrl } from '../services/apiBase';
import { getCommonStaticProps } from '../utils/translationProps';

type ScheduleFormState = {
  type: string;
  message: string;
  delivery_method: string;
  scheduled_for: string;
};

type ScheduleSubmitState = {
  processing: boolean;
  error: string | null;
};

const initialForm: ScheduleFormState = {
  type: 'scheduled_post',
  message: '',
  delivery_method: 'in_app',
  scheduled_for: '',
};

export default function Schedule() {
  const { t } = useTranslation('common');
  const [form, setForm] = useState<ScheduleFormState>(initialForm);
  const [status, setStatus] = useState<ScheduleSubmitState>({ processing: false, error: null });

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (status.processing) {
      return;
    }
    if (!form.message.trim()) {
      setStatus({ processing: false, error: t('schedule.messageRequired') });
      return;
    }
    if (!form.scheduled_for) {
      setStatus({ processing: false, error: t('schedule.whenRequired') });
      return;
    }
    const scheduled_for = new Date(form.scheduled_for).toISOString();
    setStatus({ processing: true, error: null });
    try {
      await axios.post(
        resolveApiUrl('/api/notifications/scheduled'),
        {
          message: form.message,
          type: form.type,
          scheduled_for,
          metadata: { delivery_method: form.delivery_method },
        },
        { headers: getAuthHeaders() }
      );
      setForm(initialForm);
      setStatus({ processing: false, error: null });
    } catch {
      setStatus({ processing: false, error: t('schedule.submitError') });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">{t('schedule.title')}</h1>
      {status.error && <p role="alert">{status.error}</p>}
      <form onSubmit={submit} className="space-y-4 max-w-md">
        <div>
          <label className="block mb-1" htmlFor="schedule-message">
            {t('schedule.message')}
          </label>
          <input
            id="schedule-message"
            value={form.message}
            onChange={(e) => setForm({ ...form, message: e.target.value })}
            className="border p-2 w-full"
          />
        </div>
        <div>
          <label className="block mb-1" htmlFor="schedule-type">
            {t('schedule.type')}
          </label>
          <select
            id="schedule-type"
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
          <label className="block mb-1" htmlFor="schedule-delivery">
            {t('schedule.delivery')}
          </label>
          <select
            id="schedule-delivery"
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
          <label className="block mb-1" htmlFor="schedule-when">
            {t('schedule.when')}
          </label>
          <input
            id="schedule-when"
            type="datetime-local"
            value={form.scheduled_for}
            onChange={(e) => setForm({ ...form, scheduled_for: e.target.value })}
            className="border p-2 w-full"
          />
        </div>
        <button
          type="submit"
          className="bg-blue-500 text-white px-4 py-2"
          disabled={status.processing}
        >
          {t('schedule.submit')}
        </button>
      </form>
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
