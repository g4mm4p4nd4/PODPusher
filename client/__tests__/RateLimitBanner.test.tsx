import '@testing-library/jest-dom';
import { act, render, screen } from '@testing-library/react';
import React from 'react';
import RateLimitBanner from '../components/RateLimitBanner';
import { getRateLimitState, onRateLimitChange, RateLimitState } from '../services/httpClient';

jest.mock('next-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, values?: { seconds?: number }) => {
      if (key === 'rateLimit.banner') {
        return `Rate limited for ${values?.seconds ?? 0}s`;
      }
      return key;
    },
  }),
}));

jest.mock('../services/httpClient', () => ({
  getRateLimitState: jest.fn(),
  onRateLimitChange: jest.fn(),
}));

const mockedGetRateLimitState = getRateLimitState as jest.MockedFunction<typeof getRateLimitState>;
const mockedOnRateLimitChange = onRateLimitChange as jest.MockedFunction<typeof onRateLimitChange>;

describe('RateLimitBanner', () => {
  it('renders translated countdown text when initially rate limited', () => {
    mockedGetRateLimitState.mockReturnValue({
      isLimited: true,
      retryAfter: 5,
      remaining: 0,
      limit: 100,
    });
    mockedOnRateLimitChange.mockImplementation(() => () => undefined);

    render(<RateLimitBanner />);

    expect(screen.getByRole('alert')).toHaveTextContent('Rate limited for 5s');
  });

  it('subscribes to rate-limit updates and renders translated banner text', () => {
    let listener: ((state: RateLimitState) => void) | undefined;
    mockedGetRateLimitState.mockReturnValue({
      isLimited: false,
      retryAfter: 0,
      remaining: 50,
      limit: 100,
    });
    mockedOnRateLimitChange.mockImplementation((cb) => {
      listener = cb;
      return () => undefined;
    });

    render(<RateLimitBanner />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    act(() => {
      listener?.({
        isLimited: true,
        retryAfter: 3,
        remaining: 0,
        limit: 100,
      });
    });

    expect(screen.getByRole('alert')).toHaveTextContent('Rate limited for 3s');
  });
});
