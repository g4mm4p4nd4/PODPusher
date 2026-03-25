import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';
import '@testing-library/jest-dom';
import React from 'react';
import Notifications from '../pages/notifications';
import Schedule from '../pages/schedule';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'notifications.title': 'Notifications',
        'notifications.markRead': 'Mark as read',
        'notifications.empty': 'No notifications yet',
        'notifications.loadError': 'Could not load notifications right now. Try again.',
        'notifications.processing': 'Working...',
        'notifications.updateError': 'Unable to update notification. Please try again.',
        'schedule.title': 'Schedule Notification',
        'schedule.message': 'Message',
        'schedule.type': 'Type',
        'schedule.delivery': 'Delivery Method',
        'schedule.when': 'When',
        'schedule.submit': 'Schedule',
        'schedule.messageRequired': 'Please provide a message',
        'schedule.whenRequired': 'Please select a date and time',
        'schedule.submitError': 'Could not schedule notification. Please try again.',
        'schedule.types.scheduled_post': 'Scheduled Post',
        'schedule.types.quota_reset': 'Quota Reset',
        'schedule.types.trending_product': 'Trending Product',
        'schedule.deliveryMethods.in_app': 'In App',
        'schedule.deliveryMethods.email': 'Email',
        'schedule.deliveryMethods.push': 'Push',
      };
      return translations[key] ?? key;
    },
  }),
}));

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

beforeEach(() => {
  mockedAxios.get.mockReset();
  mockedAxios.put.mockReset();
  mockedAxios.post.mockReset();
});

test('marks a notification as read when user confirms it', async () => {
  mockedAxios.get.mockResolvedValue({
    data: [
      {
        id: 42,
        message: 'New campaign is ready',
        type: 'info',
        created_at: '2026-03-23T10:00:00.000Z',
        read_status: false,
      },
    ],
  });
  mockedAxios.put.mockResolvedValue({ data: {} });

  render(<Notifications />);

  const button = await screen.findByTestId('read-42');
  fireEvent.click(button);

  await waitFor(() =>
    expect(mockedAxios.put).toHaveBeenCalledWith(
      expect.any(String),
      undefined,
      expect.objectContaining({ headers: expect.objectContaining({ 'X-User-Id': '1' }) })
    )
  );
});

test('schedules a notification with expected payload', async () => {
  mockedAxios.post.mockResolvedValue({ data: {} });

  render(<Schedule />);

  fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'Draft post reminder' } });
  fireEvent.change(screen.getByLabelText('When'), { target: { value: '2030-01-01T12:00' } });
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));

  const expectedScheduledFor = new Date('2030-01-01T12:00').toISOString();
  await waitFor(() =>
    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.any(String),
      {
        message: 'Draft post reminder',
        type: 'scheduled_post',
        scheduled_for: expectedScheduledFor,
        metadata: { delivery_method: 'in_app' },
      },
      expect.objectContaining({ headers: expect.objectContaining({ 'X-User-Id': '1' }) })
    )
  );
});

test('shows validation message for empty schedule message', async () => {
  mockedAxios.post.mockResolvedValue({ data: {} });

  render(<Schedule />);

  fireEvent.change(screen.getByLabelText('When'), { target: { value: '2030-01-01T12:00' } });
  fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('Please provide a message');
});
