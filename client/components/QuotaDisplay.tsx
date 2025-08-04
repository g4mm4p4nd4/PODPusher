import React, { useEffect, useState } from 'react';
import { fetchPlan, PlanUsage } from '../services/user';

interface Props {
  userId: number;
}

export default function QuotaDisplay({ userId }: Props) {
  const [usage, setUsage] = useState<PlanUsage | null>(null);

  useEffect(() => {
    fetchPlan(userId)
      .then(setUsage)
      .catch(() => setUsage(null));
  }, [userId]);

  const remaining = usage ? usage.limit - usage.quota_used : null;
  const warn = remaining !== null && usage && remaining <= Math.ceil(usage.limit * 0.1);

  return (
    <span data-testid="quota" className={`ml-auto text-sm ${warn ? 'text-yellow-300' : ''}`}>
      {remaining !== null ? `${remaining} credits left` : ''}
    </span>
  );
}
