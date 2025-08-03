import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

const initialData: SummaryRecord[] = [{ path: '/home', count: 1 }];

it('renders analytics chart and changes filter', async () => {
  render(<Analytics initialData={initialData} />);
  expect(screen.getByTestId('chart')).toBeInTheDocument();
  const select = screen.getByLabelText('analytics.filter');
  mockedAxios.get.mockResolvedValueOnce({ data: [{ path: '/prod', count: 2 }] });
  fireEvent.change(select, { target: { value: 'click' } });
  await waitFor(() => expect(mockedAxios.get).toHaveBeenCalledTimes(1));
});
