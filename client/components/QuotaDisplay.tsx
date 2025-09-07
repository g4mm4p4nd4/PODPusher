import React, { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { fetchPlan, PlanUsage } from '../services/user';
import { formatNumber } from '../utils/format';

export default function QuotaDisplay() {
  const { t, i18n } = useTranslation('common');
  const [usage, setUsage] = useState<PlanUsage | null>(null);

  useEffect(() => {
    fetchPlan().then(setUsage).catch((err) => console.error(err));
  }, []);

  if (!usage) {
    return <span data-testid="quota" />;
  }

  const remaining = usage.limit - usage.quota_used;
  const warn = remaining <= usage.limit * 0.1;

  return (
    <span
      data-testid="quota"
      className={`ml-auto text-sm ${warn ? 'text-red-500' : ''}`}
    >
      {t('quota.display', {
        remaining: formatNumber(remaining, i18n.language),
        limit: formatNumber(usage.limit, i18n.language),
      })}
    </span>
  );
}
