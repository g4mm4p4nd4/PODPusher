import axios from 'axios';

const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export interface PlanUsage {
  plan: string;
  quota_used: number;
  limit: number;
}

export async function fetchPlan(userId: number): Promise<PlanUsage> {
  const res = await axios.get<PlanUsage>(`${api}/api/user/plan`, {
    headers: { 'X-User-Id': String(userId) },
  });
  return res.data;
}

export async function incrementQuota(
  userId: number,
  increment: number,
): Promise<PlanUsage> {
  const res = await axios.post<PlanUsage>(
    `${api}/api/user/plan`,
    { increment },
    { headers: { 'X-User-Id': String(userId) } },
  );
  return res.data;
}
