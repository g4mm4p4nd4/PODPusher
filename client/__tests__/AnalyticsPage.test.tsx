import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';
import axios from 'axios';
import Analytics, { SummaryRecord } from '../pages/analytics';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

jest.mock('axios');

jest.mock('next/dynamic', () => () => (props: any) => <div data-testid="chart" {...props} />);

jest.mock('react-chartjs-2', () => ({
  Bar: ({}) => <div data-testid="chart" />,
}));

const mockedAxios = axios as jest.Mocked<typeof axios>;

const initialData: SummaryRecord[] = [
  { path: '/home', views: 1, clicks: 0, conversions: 0, conversion_rate: 0 },
];

it('renders analytics charts and refreshes', async () => {
  jest.useFakeTimers();
  mockedAxios.get.mockResolvedValue({ data: initialData });
  render(<Analytics initialData={initialData} />);
  expect(screen.getAllByTestId('chart')).toHaveLength(3);
  jest.advanceTimersByTime(5000);
  await waitFor(() => expect(mockedAxios.get).toHaveBeenCalled());
  jest.useRealTimers();
});
