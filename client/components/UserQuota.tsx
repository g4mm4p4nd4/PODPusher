import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  fetchCurrentUser,
  imageGeneratedEvent,
  quotaRefreshEvent,
  UserProfile,
} from '../services/user';

const REFRESH_EVENTS = [quotaRefreshEvent, imageGeneratedEvent];

const formatPlan = (plan: string) => plan.charAt(0).toUpperCase() + plan.slice(1);

export default function UserQuota() {
  const [profile, setProfile] = useState<UserProfile | null>(null);

  const loadProfile = useCallback(async () => {
    try {
      const result = await fetchCurrentUser();
      setProfile(result);
    } catch (error) {
      console.error(error);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    const handler = () => {
      void loadProfile();
    };
    REFRESH_EVENTS.forEach(event => window.addEventListener(event, handler));
    return () => {
      REFRESH_EVENTS.forEach(event => window.removeEventListener(event, handler));
    };
  }, [loadProfile]);

  const progress = useMemo(() => {
    if (!profile || profile.quota_limit == null || profile.quota_limit <= 0) {
      return null;
    }
    const safeUsed = Math.max(0, profile.quota_used);
    const safeLimit = Math.max(1, profile.quota_limit);
    const percentage = Math.min(100, Math.round((safeUsed / safeLimit) * 100));
    const remaining = Math.max(0, profile.quota_limit - profile.quota_used);
    return { percentage, remaining, used: safeUsed, limit: safeLimit };
  }, [profile]);

  if (!profile) {
    return (
      <div
        data-testid="quota"
        className="ml-auto flex w-56 flex-col gap-1 text-xs text-gray-300"
      >
        <div className="flex justify-between">
          <span className="font-medium">&nbsp;</span>
          <span>&nbsp;</span>
        </div>
        <div className="h-2 w-full animate-pulse rounded bg-gray-700" />
        <span>&nbsp;</span>
      </div>
    );
  }

  if (profile.quota_limit == null) {
    return (
      <div data-testid="quota" className="ml-auto text-sm font-medium text-green-400">
        {`${formatPlan(profile.plan)} · Unlimited`}
      </div>
    );
  }

  return (
    <div data-testid="quota" className="ml-auto flex w-56 flex-col gap-1 text-xs text-gray-200">
      <div className="flex justify-between">
        <span className="font-medium capitalize">{profile.plan}</span>
        <span>{`${progress?.used ?? 0}/${progress?.limit ?? profile.quota_limit}`}</span>
      </div>
      <div className="h-2 overflow-hidden rounded bg-gray-700" aria-hidden="true">
        <div
          data-testid="quota-bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuenow={progress?.percentage ?? 0}
          aria-valuemax={100}
          className={`h-full transition-all ${
            (progress?.percentage ?? 0) >= 90 ? 'bg-red-500' : 'bg-blue-500'
          }`}
          style={{ width: `${progress?.percentage ?? 0}%` }}
        />
      </div>
      <span>{`${progress?.remaining ?? 0} credits left`}</span>
    </div>
  );
}
