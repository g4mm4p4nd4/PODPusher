import React, { useEffect, useState } from 'react';

import {
  Button,
  LoadingState,
  PageHeader,
  Panel,
  Pill,
  ProgressBar,
} from '../components/ControlCenter';
import { DashboardResponse, fetchSettingsDashboard } from '../services/controlCenter';
import { getCommonStaticProps } from '../utils/translationProps';

const tabs = ['General', 'Localization', 'Brand Profiles', 'Integrations', 'Quotas', 'Users & Roles'];

export default function SettingsPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [activeTab, setActiveTab] = useState('Localization');

  useEffect(() => {
    fetchSettingsDashboard().then(setData).catch(() => setData(null));
  }, []);

  if (!data) return <LoadingState />;

  return (
    <div className="space-y-4">
      <PageHeader title="Settings & Localization" actions={<Button variant="primary">Save Changes</Button>} />
      <div className="flex flex-wrap gap-2 border-b border-slate-800">
        {tabs.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 text-sm ${
              activeTab === tab
                ? 'border-b-2 border-orange-500 text-orange-300'
                : 'text-slate-400 hover:text-slate-100'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.7fr_0.75fr]">
        <Panel title="Localization Settings">
          <div className="space-y-4 text-sm">
            <ReadonlyField label="Default Language" value={data.localization.default_language} />
            <ReadonlyField label="Marketplace Regions" value={data.localization.marketplace_regions.join(', ')} />
            <ReadonlyField label="Currency" value={data.localization.currency} />
            <ReadonlyField label="Date Format" value={data.localization.date_format} />
            <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <div className="flex items-center justify-between">
                <span>Localized Niche Targeting</span>
                <Pill tone={data.localization.localized_niche_targeting ? 'green' : 'slate'}>
                  {data.localization.localized_niche_targeting ? 'Enabled' : 'Off'}
                </Pill>
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="Localization Preview">
          <div className="space-y-3 text-sm">
            {Object.entries(data.localization.preview || {}).map(([key, value]) => (
              <div key={key} className="flex justify-between gap-4 border-b border-slate-800 pb-2">
                <span className="capitalize text-slate-500">{key.replace(/_/g, ' ')}</span>
                <span>{String(value)}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Regional Niche Preferences">
          <div className="space-y-3">
            {(data.regional_niche_preferences.categories || []).map((item: any) => (
              <div key={item.category}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{item.category}</span>
                  <span>{item.weight}%</span>
                </div>
                <ProgressBar value={item.weight} />
              </div>
            ))}
            <div className="pt-2">
              <p className="mb-2 text-sm text-slate-400">Excluded Global Niches</p>
              <div className="flex flex-wrap gap-2">
                {(data.regional_niche_preferences.excluded_global_niches || []).map((item: string) => (
                  <Pill key={item}>{item}</Pill>
                ))}
              </div>
            </div>
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel title="Brand Profiles" action={<Button>New Brand</Button>}>
          <div className="space-y-2">
            {(data.brand_profiles || []).map((profile: any) => (
              <div key={profile.name} className={`rounded-md border p-3 text-sm ${
                profile.active ? 'border-orange-500 bg-orange-500/10' : 'border-slate-800 bg-slate-950'
              }`}>
                <div className="flex justify-between">
                  <span className="font-medium">{profile.name}</span>
                  <Pill tone={profile.active ? 'green' : 'slate'}>{profile.active ? 'Active' : 'Inactive'}</Pill>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Integrations">
          <div className="space-y-2">
            {(data.integrations || []).map((item: any) => (
              <div key={item.provider} className="flex justify-between rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                <div>
                  <p className="font-medium capitalize">{item.provider}</p>
                  <p className="text-slate-500">{item.account_name || 'No account connected'}</p>
                </div>
                <Pill tone={item.status === 'connected' ? 'green' : item.status === 'stub' ? 'orange' : 'slate'}>
                  {item.status}
                </Pill>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Quotas & Usage">
          <QuotaLine label="Image Generation" quota={data.quotas.image_generation} tone="orange" />
          <QuotaLine label="AI Credits" quota={data.quotas.ai_credits} tone="green" />
          <QuotaLine label="Active Listings" quota={data.quotas.active_listings} tone="blue" />
          <QuotaLine label="A/B Tests" quota={data.quotas.ab_tests} tone="purple" />
        </Panel>
      </div>

      <Panel title="Users & Roles" action={<Button>Invite User</Button>}>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr>
                <th className="py-2">User</th>
                <th>Role</th>
                <th>Permissions</th>
                <th>Last Active</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(data.team_members || []).map((member: any) => (
                <tr key={member.email} className="border-t border-slate-800">
                  <td className="py-3">
                    <p className="font-medium">{member.name}</p>
                    <p className="text-slate-500">{member.email}</p>
                  </td>
                  <td><Pill tone="purple">{member.role}</Pill></td>
                  <td>{(member.permissions || []).join(', ')}</td>
                  <td>{new Date(member.last_active_at).toLocaleString()}</td>
                  <td><Pill tone="green">{member.status}</Pill></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function ReadonlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-slate-100">{value}</p>
    </div>
  );
}

function QuotaLine({
  label,
  quota,
  tone,
}: {
  label: string;
  quota: any;
  tone: 'orange' | 'green' | 'blue' | 'purple';
}) {
  const percent = quota?.percent ?? Math.round(((quota?.used || 0) / Math.max(1, quota?.limit || 1)) * 100);
  return (
    <div className="mb-4">
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <span className="text-slate-500">{quota?.used || 0} / {quota?.limit || 0}</span>
      </div>
      <ProgressBar value={percent} tone={tone} />
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
