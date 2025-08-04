import axios from 'axios';

const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export interface PlanUsage {
  plan: string;
  quota_used: number;
  limit: number;
}

export async function fetchPlan(): Promise<PlanUsage> {
  const res = await axios.get<PlanUsage>(`${api}/api/user/plan`, {
    headers: { 'X-User-Id': '1' },
  });
  return res.data;
}

export async function incrementQuota(count: number): Promise<PlanUsage> {
  const res = await axios.post<PlanUsage>(
    `${api}/api/user/plan`,
    { count },
    { headers: { 'X-User-Id': '1' } }
  );
  return res.data;
}
