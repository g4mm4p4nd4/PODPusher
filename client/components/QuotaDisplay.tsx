import React, { useEffect, useState } from 'react';
import { fetchPlan, PlanUsage } from '../services/user';

export default function QuotaDisplay() {
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
      {`${remaining}/${usage.limit} credits`}
    </span>
  );
}
