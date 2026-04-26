import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import axios from 'axios';

import SeasonalEventsPage from '../pages/seasonal-events';

jest.mock('axios');

jest.mock('next/router', () => ({
  useRouter: () => ({ query: {} }),
}));

const mockedAxios = axios as jest.Mocked<typeof axios>;

function seasonalPayload() {
  return {
    opportunity_score: 87,
    listings_to_prepare: 26,
    events: [
      {
        name: 'Back to School',
        event_date: '2026-08-01',
        days_away: 99,
        priority: 'high',
        opportunity_score: 88,
        saved: false,
        recommended_keywords: [
          { keyword: 'back to school', volume: 54200 },
          { keyword: 'teacher life', volume: 15400 },
        ],
        product_categories: [
          { category: 'T-Shirts', listings: 15200, demand: 88 },
          { category: 'Mugs', listings: 5300, demand: 70 },
        ],
        niche_angles: ['Teacher Appreciation', 'Student Motivation'],
      },
    ],
    high_priority_events: [
      {
        name: 'Back to School',
        event_date: '2026-08-01',
        days_away: 99,
        priority: 'high',
        recommended_keywords: [{ keyword: 'back to school', volume: 54200 }],
        product_categories: [{ category: 'T-Shirts', listings: 15200, demand: 88 }],
        niche_angles: ['Teacher Appreciation'],
      },
    ],
    timeline: [
      {
        name: 'Back to School',
        event_date: '2026-08-01',
        start_by: '2026-06-17',
        launch_window: '17-47 days before event',
        priority: 'high',
      },
    ],
    provenance: { source: 'seasonal_calendar', is_estimated: true, updated_at: '', confidence: 0.7 },
  };
}

describe('seasonal events page', () => {
  beforeEach(() => {
    mockedAxios.get.mockReset();
    mockedAxios.post.mockReset();
    mockedAxios.get.mockResolvedValue({ data: seasonalPayload() });
    mockedAxios.post.mockResolvedValue({ data: { id: 1, name: 'Back to School', saved: true } });
  });

  it('reloads when category and horizon filters change', async () => {
    render(<SeasonalEventsPage />);

    await screen.findByText('Seasonal Events Calendar');
    fireEvent.change(screen.getByLabelText('Category'), { target: { value: 'Apparel' } });

    await waitFor(() =>
      expect(mockedAxios.get).toHaveBeenLastCalledWith(
        'http://localhost:8000/api/seasonal/events',
        expect.objectContaining({
          params: expect.objectContaining({ category: 'Apparel' }),
        })
      )
    );

    fireEvent.change(screen.getByLabelText('Time Horizon'), { target: { value: '12' } });
    await waitFor(() =>
      expect(mockedAxios.get).toHaveBeenLastCalledWith(
        'http://localhost:8000/api/seasonal/events',
        expect.objectContaining({
          params: expect.objectContaining({ horizon_months: 12 }),
        })
      )
    );
  });

  it('shows selected event details and saves the event', async () => {
    render(<SeasonalEventsPage />);

    await screen.findByText('Recommended Keywords');
    expect(screen.getByText('Teacher Appreciation')).toBeInTheDocument();
    expect(screen.getByText('Listing Count Opportunity')).toBeInTheDocument();
    expect(screen.getByText('Use in Composer')).toHaveAttribute(
      'href',
      expect.stringContaining('/listing-composer?source=seasonal')
    );

    fireEvent.click(screen.getByRole('button', { name: 'Add to My Events' }));
    await waitFor(() =>
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/seasonal/events/save',
        { name: 'Back to School' },
        expect.any(Object)
      )
    );
    expect(await screen.findByText('Back to School saved to My Events.')).toBeInTheDocument();
    expect(screen.getAllByText('Saved').length).toBeGreaterThan(0);
  });

  it('supports month navigation and today reset controls', async () => {
    render(<SeasonalEventsPage />);

    await screen.findByRole('button', { name: 'Next' });
    const initialMonth = screen.getByRole('heading', { name: /\w+ \d{4}/ }).textContent;
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(screen.getByRole('heading', { name: /\w+ \d{4}/ }).textContent).not.toEqual(initialMonth);
    fireEvent.click(screen.getByRole('button', { name: 'Today' }));
    expect(screen.getByText('High Priority')).toBeInTheDocument();
  });
});
