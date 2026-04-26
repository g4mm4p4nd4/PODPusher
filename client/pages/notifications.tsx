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
import {
  createAutomationJob,
  updateNotificationPreferences,
  updateNotificationRule,
} from '../services/operations';
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
  const [statusMessage, setStatusMessage] = useState('');
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [scheduleName, setScheduleName] = useState('Weekly Digest');
  const [scheduleFrequency, setScheduleFrequency] = useState('Weekly (Fri 9 AM)');
  const [saving, setSaving] = useState<string | null>(null);

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
    setSaving('rule');
    try {
      await createNotificationRule({
        name: ruleName,
        metric: 'image_quota_remaining',
        operator: 'less_than',
        threshold: 20,
        window: '1 day',
        channels: ['Email', 'In-App'],
        active: true,
      });
      setStatusMessage('Alert rule saved.');
      await load();
    } finally {
      setSaving(null);
    }
  };

  const createSchedule = async () => {
    setSaving('schedule');
    try {
      const nextRun = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
      await createAutomationJob({
        name: scheduleName,
        frequency: scheduleFrequency,
        next_run: nextRun,
        category: 'digest',
        metadata: { source: 'notifications_scheduler_ui' },
      });
      setStatusMessage('Schedule saved and queued for the next run.');
      setScheduleOpen(false);
      await load();
    } finally {
      setSaving(null);
    }
  };

  const toggleRule = async (rule: any) => {
    setSaving(`rule-${rule.id}`);
    try {
      if (rule.id) {
        await updateNotificationRule(rule.id, { active: !rule.active });
      } else {
        await createNotificationRule({ ...rule, active: !rule.active });
      }
      setStatusMessage('Alert rule updated.');
      await load();
    } finally {
      setSaving(null);
    }
  };

  const savePreferences = async (channel: 'email' | 'in_app', enabled: boolean) => {
    setSaving(channel);
    try {
      const payload =
        channel === 'email'
          ? { email_enabled: enabled, in_app_enabled: data?.preferences?.in_app?.enabled ?? true }
          : { in_app_enabled: enabled, email_enabled: data?.preferences?.email?.enabled ?? true };
      const updated = await updateNotificationPreferences(payload);
      setData((current) => (current ? { ...current, preferences: updated } : current));
      setStatusMessage('Notification preferences saved.');
    } finally {
      setSaving(null);
    }
  };

  const configureSlack = async () => {
    setStatusMessage('Slack is unavailable in local mode until credentials are configured.');
  };

  if (loading || !data) return <LoadingState />;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Notifications & Scheduler"
        subtitle="Manage automated alerts, digests, and scheduled jobs."
      />
      {statusMessage ? (
        <div role="status" className="rounded-md border border-emerald-500/30 bg-emerald-950/50 p-3 text-sm text-emerald-200">
          {statusMessage}
        </div>
      ) : null}
      {data.cards?.length ? <MetricGrid metrics={data.cards} /> : null}

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel
          title="Digest Schedule"
          action={<Button onClick={() => setScheduleOpen((value) => !value)}>Manage Schedules</Button>}
        >
          {scheduleOpen ? (
            <div className="mb-4 grid gap-2 rounded-md border border-slate-800 bg-slate-950 p-3 md:grid-cols-[1fr_1fr_auto]">
              <label className="text-xs text-slate-400">
                Schedule name
                <input
                  value={scheduleName}
                  onChange={(event) => setScheduleName(event.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 p-2 text-sm text-slate-100 outline-none"
                />
              </label>
              <label className="text-xs text-slate-400">
                Frequency
                <select
                  value={scheduleFrequency}
                  onChange={(event) => setScheduleFrequency(event.target.value)}
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 p-2 text-sm text-slate-100 outline-none"
                >
                  <option>Daily</option>
                  <option>Every 6 hours</option>
                  <option>Weekly (Fri 9 AM)</option>
                  <option>Monthly</option>
                </select>
              </label>
              <div className="flex items-end">
                <Button onClick={createSchedule} disabled={saving === 'schedule'} variant="primary">
                  {saving === 'schedule' ? 'Saving...' : 'Save'}
                </Button>
              </div>
            </div>
          ) : null}
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
                    <td>
                      <button
                        type="button"
                        onClick={() => {
                          setScheduleName(item.digest);
                          setScheduleFrequency(item.schedule);
                          setScheduleOpen(true);
                        }}
                      >
                        <Pill tone={item.active ? 'green' : 'slate'}>{item.active ? 'Active' : 'Off'}</Pill>
                      </button>
                    </td>
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
                  {!item.read_status && item.id ? (
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

        <Panel title="Rule Builder" action={<Button onClick={addRule} disabled={saving === 'rule'}>{saving === 'rule' ? 'Saving...' : 'New Rule'}</Button>}>
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
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{rule.name}</p>
                    <p className="text-slate-500">{rule.metric} {rule.operator} {rule.threshold}</p>
                    <p className="mt-1 text-xs text-slate-500">{(rule.channels || []).join(' + ')} for {rule.window}</p>
                  </div>
                  <Button onClick={() => toggleRule(rule)} disabled={saving === `rule-${rule.id}`}>
                    {rule.active ? 'Disable' : 'Enable'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Upcoming Schedule">
          <div className="grid grid-cols-[64px_repeat(7,1fr)] gap-px overflow-hidden rounded-md border border-slate-800 bg-slate-800 text-xs">
            <span className="bg-slate-950 p-2 text-slate-500">Time</span>
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => <span key={day} className="bg-slate-950 p-2 text-slate-400">{day}</span>)}
            {['6:00 AM', '9:00 AM', '12:00 PM', '3:00 PM', '6:00 PM'].map((time, timeIndex) => (
              <React.Fragment key={time}>
                <span className="bg-slate-950 p-2 text-slate-500">{time}</span>
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, dayIndex) => {
                  const job = (data.upcoming_schedule || [])[(timeIndex + dayIndex) % Math.max(1, (data.upcoming_schedule || []).length)];
                  const show = job && (timeIndex + dayIndex) % 4 === 0;
                  return (
                    <span key={`${time}-${day}`} className="min-h-[44px] bg-slate-950 p-1">
                      {show ? <Pill tone={job.category === 'maintenance' ? 'orange' : 'blue'}>{job.name}</Pill> : null}
                    </span>
                  );
                })}
              </React.Fragment>
            ))}
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
          <Preference
            title="Email Notifications"
            enabled={data.preferences?.email?.enabled}
            saving={saving === 'email'}
            onToggle={(enabled) => savePreferences('email', enabled)}
          />
          <Preference
            title="In-App Notifications"
            enabled={data.preferences?.in_app?.enabled}
            saving={saving === 'in_app'}
            onToggle={(enabled) => savePreferences('in_app', enabled)}
          />
          <Preference
            title="Slack Integration"
            enabled={data.preferences?.slack?.enabled}
            onToggle={configureSlack}
            unavailable={!data.preferences?.slack?.connected}
          />
          <Preference title="Digest Preferences" enabled onToggle={() => setScheduleOpen(true)} />
        </div>
      </Panel>
    </div>
  );
}

function Preference({
  title,
  enabled,
  saving = false,
  unavailable = false,
  onToggle,
}: {
  title: string;
  enabled?: boolean;
  saving?: boolean;
  unavailable?: boolean;
  onToggle?: (enabled: boolean) => void;
}) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950 p-4">
      <div className="flex items-center justify-between">
        <span className="font-medium">{title}</span>
        <button type="button" onClick={() => onToggle?.(!enabled)} disabled={saving}>
          <Pill tone={enabled ? 'green' : unavailable ? 'orange' : 'slate'}>
            {saving ? 'Saving' : unavailable ? 'Needs setup' : enabled ? 'On' : 'Off'}
          </Pill>
        </button>
      </div>
      <div className="mt-3 space-y-1 text-sm text-slate-500">
        <p>Critical Alerts</p>
        <p>Warnings</p>
        <p>Info & Updates</p>
        {unavailable ? <p className="text-orange-300">Credential-backed setup is unavailable in local mode.</p> : null}
      </div>
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
