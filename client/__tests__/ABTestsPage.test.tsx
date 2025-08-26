import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import axios from 'axios';
import ABTests from '../pages/ab_tests';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key.split('.').pop() })
}));

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

test('submits experiment with weights', async () => {
  mockedAxios.post.mockResolvedValueOnce({ data: { id: 1 } });
  mockedAxios.get.mockResolvedValueOnce({ data: [] });
  render(<ABTests metrics={[]} />);
  fireEvent.change(screen.getByPlaceholderText('name'), { target: { value: 'Test' } });
  fireEvent.change(screen.getByPlaceholderText('variants'), { target: { value: 'A,B' } });
  fireEvent.change(screen.getByPlaceholderText('weights'), { target: { value: '0.6,0.4' } });
  fireEvent.click(screen.getByText('create'));
  expect(mockedAxios.post).toHaveBeenCalledWith(
    expect.stringContaining('/ab_tests'),
    expect.objectContaining({
      name: 'Test',
      variants: ['A', 'B'],
      experiment_type: 'image',
      traffic_split: [0.6, 0.4],
    })
  );
});
