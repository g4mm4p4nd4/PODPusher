import axios from 'axios';
import React, { useEffect, useState } from 'react';

import {
  Button,
  LoadingState,
  MetricGrid,
  PageHeader,
  Panel,
  Pill,
} from '../components/ControlCenter';
import {
  DashboardResponse,
  createNotificationRule,
  fetchNotificationsDashboard,
} from '../services/controlCenter';
import { getAuthHeaders, resolveApiUrl } from '../services/apiBase';
import { getCommonStaticProps } from '../utils/translationProps';

type NotificationItem = {
  id: number;
  message: string;
  type: string;
  created_at: string;
  read_status: boolean;
};

export default function Notifications() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [ruleName, setRuleName] = useState('Low Image Quota Warning');

  const normalize = (raw: any): DashboardResponse => {
    if (Array.isArray(raw)) {
      return { notifications: raw, cards: [], scheduled_jobs: [], digest_schedule: [], rules: [] };
    }
    return raw;
  };

  const load = async () => {
    setLoading(true);
    setData(normalize(await fetchNotificationsDashboard()));
    setLoading(false);
  };

  useEffect(() => {
    void load();
  }, []);

  const markRead = async (id: number) => {
    await axios.put(resolveApiUrl(`/api/notifications/${id}/read`), undefined, {
      headers: getAuthHeaders(),
    });
    setData((current) => {
      if (!current) return current;
      return {
        ...current,
        notifications: (current.notifications || []).map((item: NotificationItem) =>
          item.id === id ? { ...item, read_status: true } : item
        ),
      };
    });
  };

  const addRule = async () => {
    await createNotificationRule({
      name: ruleName,
      metric: 'image_quota_remaining',
      operator: 'less_than',
      threshold: 20,
      window: '1 day',
      channels: ['Email', 'In-App'],
      active: true,
    });
    await load();
  };

  if (loading || !data) return <LoadingState />;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Notifications & Scheduler"
        subtitle="Manage automated alerts, digests, and scheduled jobs."
      />
      {data.cards?.length ? <MetricGrid metrics={data.cards} /> : null}

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Digest Schedule" action={<Button>Manage Schedules</Button>}>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-slate-500">
                <tr>
                  <th className="py-2">Digest</th>
                  <th>Schedule</th>
                  <th>Audience</th>
                  <th>Channels</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {(data.digest_schedule || []).map((item: any) => (
                  <tr key={item.digest} className="border-t border-slate-800">
                    <td className="py-3 font-medium">{item.digest}</td>
                    <td>{item.schedule}</td>
                    <td>{item.audience}</td>
                    <td>{(item.channels || []).join(', ')}</td>
                    <td><Pill tone={item.active ? 'green' : 'slate'}>{item.active ? 'Active' : 'Off'}</Pill></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Scheduled Jobs">
          <div className="space-y-2">
            {(data.scheduled_jobs || []).map((job: any) => (
              <div key={`${job.id}-${job.name}`} className="grid grid-cols-[1fr_120px_90px] gap-2 rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                <span className="font-medium">{job.name}</span>
                <span className="text-slate-500">{job.frequency}</span>
                <Pill tone={job.status === 'on_track' ? 'green' : 'orange'}>{job.status}</Pill>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.85fr_0.75fr_1fr]">
        <Panel title="Notifications Feed">
          <div className="space-y-2">
            {(data.notifications || []).map((item: NotificationItem) => (
              <div
                key={`${item.id}-${item.message}`}
                className={`rounded-md border border-slate-800 bg-slate-950 p-3 text-sm ${
                  item.read_status ? 'opacity-60' : ''
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <Pill tone={item.type === 'warning' ? 'orange' : item.type === 'success' ? 'green' : 'blue'}>{item.type}</Pill>
                    <p className="mt-2">{item.message}</p>
                  </div>
                  {!item.read_status ? (
                    <button
                      type="button"
                      data-testid={`read-${item.id}`}
                      onClick={() => markRead(item.id)}
                      className="text-sm text-blue-400"
                    >
                      Mark as read
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Rule Builder" action={<Button onClick={addRule}>New Rule</Button>}>
          <label className="block text-sm text-slate-300">
            Rule name
            <input
              value={ruleName}
              onChange={(event) => setRuleName(event.target.value)}
              className="mt-1 w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none"
            />
          </label>
          <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
            <Pill>IF image quota</Pill>
            <Pill>less than</Pill>
            <Pill>20%</Pill>
            <Pill>Email</Pill>
            <Pill>In-App</Pill>
            <Pill tone="green">Active</Pill>
          </div>
          <div className="mt-4 space-y-2">
            {(data.rules || []).map((rule: any) => (
              <div key={`${rule.id}-${rule.name}`} className="rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                <p className="font-medium">{rule.name}</p>
                <p className="text-slate-500">{rule.metric} {rule.operator} {rule.threshold}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Upcoming Schedule">
          <div className="grid grid-cols-7 gap-1 text-xs text-slate-500">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => <span key={day}>{day}</span>)}
          </div>
          <div className="mt-3 space-y-2">
            {(data.upcoming_schedule || []).map((job: any) => (
              <div key={`${job.name}-timeline`} className="rounded-md border border-slate-800 bg-slate-950 p-2 text-sm">
                <span className="text-slate-300">{job.name}</span>
                <span className="ml-2 text-slate-500">{new Date(job.next_run).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Notification Preferences">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Preference title="Email Notifications" enabled={data.preferences?.email?.enabled} />
          <Preference title="In-App Notifications" enabled={data.preferences?.in_app?.enabled} />
          <Preference title="Slack Integration" enabled={data.preferences?.slack?.enabled} />
          <Preference title="Digest Preferences" enabled />
        </div>
      </Panel>
    </div>
  );
}

function Preference({ title, enabled }: { title: string; enabled?: boolean }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950 p-4">
      <div className="flex items-center justify-between">
        <span className="font-medium">{title}</span>
        <Pill tone={enabled ? 'green' : 'slate'}>{enabled ? 'On' : 'Off'}</Pill>
      </div>
      <div className="mt-3 space-y-1 text-sm text-slate-500">
        <p>Critical Alerts</p>
        <p>Warnings</p>
        <p>Info & Updates</p>
      </div>
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
