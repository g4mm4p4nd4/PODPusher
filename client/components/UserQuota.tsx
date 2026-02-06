import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'next-i18next';
import {
  fetchCurrentUser,
  imageGeneratedEvent,
  quotaRefreshEvent,
  UserProfile,
} from '../services/user';

const REFRESH_EVENTS = [quotaRefreshEvent, imageGeneratedEvent];

const formatPlan = (plan: string) => plan.charAt(0).toUpperCase() + plan.slice(1);

/**
 * Tier-based quota breakdown. Mirrors services/common/quotas.py PLAN_LIMITS.
 * Shows how the total quota is distributed across resource types.
 */
const PLAN_BREAKDOWN: Record<string, { listings: number; images: number; ideas: number }> = {
  free: { listings: 10, images: 20, ideas: 50 },
  starter: { listings: 50, images: 100, ideas: 200 },
  professional: { listings: 200, images: 500, ideas: 1000 },
  enterprise: { listings: 1000, images: 2500, ideas: 5000 },
};

export default function UserQuota() {
  const { t } = useTranslation('common');
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

  const breakdown = useMemo(() => {
    if (!profile) return null;
    return PLAN_BREAKDOWN[profile.plan] ?? PLAN_BREAKDOWN.free;
  }, [profile]);

  const handleUpgrade = () => {
    window.location.href = '/api/billing/portal';
  };

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
    <div data-testid="quota" className="ml-auto flex w-72 flex-col gap-2 text-xs text-gray-200">
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
      <span>{t('settings.creditsLeft', { count: progress?.remaining ?? 0 })}</span>

      {/* Usage Breakdown by Resource Type */}
      {breakdown && (
        <div data-testid="quota-breakdown" className="mt-2 space-y-1">
          <p className="text-xs font-semibold text-gray-400">
            {t('settings.usageBreakdown')}
          </p>
          <div className="flex justify-between text-gray-300">
            <span>{t('settings.listings_quota')}</span>
            <span>{breakdown.listings}</span>
          </div>
          <div className="flex justify-between text-gray-300">
            <span>{t('settings.images_quota')}</span>
            <span>{breakdown.images}</span>
          </div>
          <div className="flex justify-between text-gray-300">
            <span>{t('settings.ideas_quota')}</span>
            <span>{breakdown.ideas}</span>
          </div>
        </div>
      )}

      {/* Upgrade CTA */}
      {profile.plan !== 'enterprise' && (
        <button
          data-testid="upgrade-cta"
          type="button"
          onClick={handleUpgrade}
          className="mt-2 w-full rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 transition-colors"
        >
          {t('settings.upgrade')}
        </button>
      )}
    </div>
  );
}
