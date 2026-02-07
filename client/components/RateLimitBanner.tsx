import React, { useEffect, useState } from 'react';
import { getRateLimitState, onRateLimitChange, RateLimitState } from '../services/httpClient';

/**
 * RateLimitBanner — displays a countdown banner when the user is rate-limited.
 *
 * Owner: Frontend-Coder (per DEVELOPMENT_PLAN.md Task 2.2.3)
 */
export default function RateLimitBanner() {
  const [state, setState] = useState<RateLimitState>(getRateLimitState());
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    const unsubscribe = onRateLimitChange((newState) => {
      setState(newState);
      if (newState.isLimited) {
        setCountdown(newState.retryAfter);
      }
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  if (!state.isLimited || countdown <= 0) return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 bg-yellow-100 border-b border-yellow-300 text-yellow-800 px-4 py-2 text-center text-sm z-50"
      role="alert"
      data-testid="rate-limit-banner"
    >
      Too many requests. Please wait {countdown}s before trying again.
    </div>
  );
}
