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
import {
  configureIntegration,
  createSettingsBrandProfile,
  fetchUsageLedger,
  inviteSettingsUser,
  saveSettingsLocalization,
  setDefaultBrandProfile,
  updateSettingsUserRole,
} from '../services/operations';
import { getCommonStaticProps } from '../utils/translationProps';

const tabs = ['General', 'Localization', 'Brand Profiles', 'Integrations', 'Quotas', 'Users & Roles'];
const roles = ['Administrator', 'Manager', 'Editor', 'Viewer'];

export default function SettingsPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [activeTab, setActiveTab] = useState('Localization');
  const [statusMessage, setStatusMessage] = useState('');
  const [saving, setSaving] = useState<string | null>(null);
  const [usageLedger, setUsageLedger] = useState<any[] | null>(null);

  useEffect(() => {
    fetchSettingsDashboard().then(setData).catch(() => setData(null));
  }, []);

  if (!data) return <LoadingState />;

  const updateLocalization = (field: string, value: unknown) => {
    setData((current) =>
      current
        ? {
            ...current,
            localization: {
              ...current.localization,
              [field]: value,
            },
          }
        : current
    );
  };

  const saveLocalization = async () => {
    setSaving('localization');
    try {
      const response: any = await saveSettingsLocalization(data.localization);
      setData((current) =>
        current ? { ...current, localization: response.localization || current.localization } : current
      );
      setStatusMessage('Localization settings saved.');
    } finally {
      setSaving(null);
    }
  };

  const createBrandProfile = async () => {
    setSaving('brand');
    try {
      const response: any = await createSettingsBrandProfile({
        name: 'New Brand Profile',
        tone: 'Friendly, Clear',
        audience: 'Niche shoppers',
        interests: ['Seasonal trends'],
        banned_topics: ['Politics'],
        preferred_products: ['Apparel', 'Mugs'],
        region: data.localization.primary_targeting_region || 'US',
        language: data.localization.default_language || 'en',
        active: false,
      });
      setData((current) =>
        current
          ? { ...current, brand_profiles: [...(current.brand_profiles || []), response.profile] }
          : current
      );
      setStatusMessage('Brand profile created.');
    } finally {
      setSaving(null);
    }
  };

  const activateBrandProfile = async (profile: any) => {
    if (!profile.id) {
      setStatusMessage('Demo profile selected. Create a brand profile to persist this default.');
      return;
    }
    setSaving(`brand-${profile.id}`);
    try {
      const response: any = await setDefaultBrandProfile(profile.id);
      setData((current) =>
        current
          ? {
              ...current,
              brand_profiles: (current.brand_profiles || []).map((item: any) => ({
                ...item,
                active: item.id === response.profile.id,
              })),
            }
          : current
      );
      setStatusMessage('Default brand profile updated.');
    } finally {
      setSaving(null);
    }
  };

  const configureProvider = async (provider: string) => {
    setSaving(`integration-${provider}`);
    try {
      const response: any = await configureIntegration(provider, { action: 'configure' });
      setStatusMessage(response.message || `${provider} configuration is unavailable in local mode.`);
    } finally {
      setSaving(null);
    }
  };

  const loadUsageLedger = async () => {
    setSaving('usage');
    try {
      const response: any = await fetchUsageLedger();
      setUsageLedger(response.items || []);
      setStatusMessage(response.demo_state ? 'Usage ledger is showing explicit demo data.' : 'Usage ledger loaded.');
    } finally {
      setSaving(null);
    }
  };

  const inviteUser = async () => {
    setSaving('invite');
    try {
      const response: any = await inviteSettingsUser({
        email: `new.user.${Date.now()}@podpusher.com`,
        role: 'Viewer',
        permissions: ['Analytics'],
      });
      setData((current) =>
        current
          ? { ...current, team_members: [...(current.team_members || []), response.member] }
          : current
      );
      setStatusMessage('Invite created with pending team-member status.');
    } finally {
      setSaving(null);
    }
  };

  const changeRole = async (member: any, role: string) => {
    if (!member.id) {
      setStatusMessage('Demo team member role is not persisted until the member is invited.');
      return;
    }
    setSaving(`member-${member.id}`);
    try {
      const response: any = await updateSettingsUserRole(member.id, {
        role,
        permissions: member.permissions,
        status: member.status,
      });
      setData((current) =>
        current
          ? {
              ...current,
              team_members: (current.team_members || []).map((item: any) =>
                item.id === response.member.id ? response.member : item
              ),
            }
          : current
      );
      setStatusMessage('Team role updated.');
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Settings & Localization"
        actions={
          <Button onClick={saveLocalization} disabled={saving === 'localization'} variant="primary">
            {saving === 'localization' ? 'Saving...' : 'Save Changes'}
          </Button>
        }
      />
      {statusMessage ? (
        <div role="status" className="rounded-md border border-emerald-500/30 bg-emerald-950/50 p-3 text-sm text-emerald-200">
          {statusMessage}
        </div>
      ) : null}
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

      {activeTab === 'General' ? <GeneralTab data={data} /> : null}
      {activeTab === 'Localization' ? (
        <LocalizationTab data={data} updateLocalization={updateLocalization} />
      ) : null}
      {activeTab === 'Brand Profiles' ? (
        <BrandProfilesTab
          profiles={data.brand_profiles || []}
          onCreate={createBrandProfile}
          onActivate={activateBrandProfile}
          saving={saving}
        />
      ) : null}
      {activeTab === 'Integrations' ? (
        <IntegrationsTab
          integrations={data.integrations || []}
          onConfigure={configureProvider}
          saving={saving}
        />
      ) : null}
      {activeTab === 'Quotas' ? (
        <QuotasTab
          quotas={data.quotas || {}}
          usage={data.usage || {}}
          usageLedger={usageLedger}
          onLoadUsage={loadUsageLedger}
          saving={saving === 'usage'}
        />
      ) : null}
      {activeTab === 'Users & Roles' ? (
        <UsersTab
          members={data.team_members || []}
          onInvite={inviteUser}
          onRoleChange={changeRole}
          saving={saving}
        />
      ) : null}
    </div>
  );
}

function GeneralTab({ data }: { data: DashboardResponse }) {
  return (
    <div className="grid gap-4 xl:grid-cols-3">
      <Panel title="Workspace">
        <div className="space-y-3 text-sm">
          {(data.stores || []).map((store: any) => (
            <div key={`${store.name}-${store.marketplace}`} className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <p className="font-medium">{store.name}</p>
              <p className="text-slate-500">{store.marketplace} / {store.region}</p>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Active Brand">
        <p className="text-sm text-slate-300">
          {(data.brand_profiles || []).find((profile: any) => profile.active)?.name || 'No active brand'}
        </p>
      </Panel>
      <Panel title="Integration Honesty">
        <p className="text-sm text-slate-400">
          Credential-backed providers stay non-blocking. Disconnected providers report fallback status instead of failing dashboard pages.
        </p>
      </Panel>
    </div>
  );
}

function LocalizationTab({
  data,
  updateLocalization,
}: {
  data: DashboardResponse;
  updateLocalization: (field: string, value: unknown) => void;
}) {
  const localization = data.localization || {};
  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_0.7fr_0.75fr]">
      <Panel title="Localization Settings">
        <div className="space-y-4 text-sm">
          <SelectField
            label="Default Language"
            value={localization.default_language}
            onChange={(value) => updateLocalization('default_language', value)}
            options={['en', 'es', 'fr', 'de']}
          />
          <TextField
            label="Marketplace Regions"
            value={(localization.marketplace_regions || []).join(', ')}
            onChange={(value) =>
              updateLocalization(
                'marketplace_regions',
                value.split(',').map((item) => item.trim()).filter(Boolean)
              )
            }
          />
          <SelectField
            label="Currency"
            value={localization.currency}
            onChange={(value) => updateLocalization('currency', value)}
            options={['USD', 'EUR', 'GBP', 'CAD', 'AUD']}
          />
          <SelectField
            label="Date Format"
            value={localization.date_format}
            onChange={(value) => updateLocalization('date_format', value)}
            options={['MMM DD, YYYY', 'DD MMM YYYY', 'YYYY-MM-DD']}
          />
          <div className="rounded-md border border-slate-800 bg-slate-950 p-3">
            <div className="flex items-center justify-between">
              <span>Localized Niche Targeting</span>
              <button
                type="button"
                onClick={() =>
                  updateLocalization('localized_niche_targeting', !localization.localized_niche_targeting)
                }
              >
                <Pill tone={localization.localized_niche_targeting ? 'green' : 'slate'}>
                  {localization.localized_niche_targeting ? 'Enabled' : 'Off'}
                </Pill>
              </button>
            </div>
          </div>
          <SelectField
            label="Primary Targeting Region"
            value={localization.primary_targeting_region}
            onChange={(value) => updateLocalization('primary_targeting_region', value)}
            options={['US', 'CA', 'GB', 'DE', 'FR', 'ES']}
          />
        </div>
      </Panel>

      <Panel title="Localization Preview">
        <div className="space-y-3 text-sm">
          {Object.entries(localization.preview || {}).map(([key, value]) => (
            <div key={key} className="flex justify-between gap-4 border-b border-slate-800 pb-2">
              <span className="capitalize text-slate-500">{key.replace(/_/g, ' ')}</span>
              <span>{String(value)}</span>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Regional Niche Preferences">
        <div className="space-y-3">
          {(data.regional_niche_preferences?.categories || []).map((item: any) => (
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
              {(data.regional_niche_preferences?.excluded_global_niches || []).map((item: string) => (
                <Pill key={item}>{item}</Pill>
              ))}
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
}

function BrandProfilesTab({
  profiles,
  onCreate,
  onActivate,
  saving,
}: {
  profiles: any[];
  onCreate: () => void;
  onActivate: (profile: any) => void;
  saving: string | null;
}) {
  return (
    <Panel title="Brand Profiles" action={<Button onClick={onCreate} disabled={saving === 'brand'}>New Brand</Button>}>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {profiles.map((profile: any) => (
          <div key={`${profile.id}-${profile.name}`} className={`rounded-md border p-3 text-sm ${
            profile.active ? 'border-orange-500 bg-orange-500/10' : 'border-slate-800 bg-slate-950'
          }`}>
            <div className="flex justify-between gap-3">
              <span className="font-medium">{profile.name}</span>
              <Pill tone={profile.active ? 'green' : 'slate'}>{profile.active ? 'Active' : 'Inactive'}</Pill>
            </div>
            <p className="mt-2 text-slate-500">{profile.tone || 'Tone not set'}</p>
            <p className="text-slate-500">{profile.audience || 'Audience not set'}</p>
            <Button onClick={() => onActivate(profile)} disabled={saving === `brand-${profile.id}`}>
              Make Default
            </Button>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function IntegrationsTab({
  integrations,
  onConfigure,
  saving,
}: {
  integrations: any[];
  onConfigure: (provider: string) => void;
  saving: string | null;
}) {
  return (
    <Panel title="Integrations">
      <div className="grid gap-3 md:grid-cols-2">
        {integrations.map((item: any) => (
          <div key={item.provider} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
            <div>
              <p className="font-medium capitalize">{item.provider}</p>
              <p className="text-slate-500">{item.account_name || 'No account connected'}</p>
              {item.status !== 'connected' ? (
                <p className="text-xs text-orange-300">Non-blocking fallback data is active.</p>
              ) : null}
            </div>
            <div className="flex items-center gap-2">
              <Pill tone={item.status === 'connected' ? 'green' : item.status === 'stub' ? 'orange' : 'slate'}>
                {item.status}
              </Pill>
              <Button onClick={() => onConfigure(item.provider)} disabled={saving === `integration-${item.provider}`}>
                Configure
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function QuotasTab({
  quotas,
  usage,
  usageLedger,
  onLoadUsage,
  saving,
}: {
  quotas: any;
  usage: Record<string, number>;
  usageLedger: any[] | null;
  onLoadUsage: () => void;
  saving: boolean;
}) {
  return (
    <div className="grid gap-4 xl:grid-cols-[0.8fr_1fr]">
      <Panel title="Quotas & Usage" action={<Button onClick={onLoadUsage} disabled={saving}>View Usage Details</Button>}>
        <QuotaLine label="Image Generation" quota={quotas.image_generation} tone="orange" />
        <QuotaLine label="AI Credits" quota={quotas.ai_credits} tone="green" />
        <QuotaLine label="Active Listings" quota={quotas.active_listings} tone="blue" />
        <QuotaLine label="A/B Tests" quota={quotas.ab_tests} tone="purple" />
      </Panel>
      <Panel title="Usage Ledger">
        {usageLedger ? (
          <div className="space-y-2">
            {usageLedger.map((item: any, index: number) => (
              <div key={`${item.resource_type}-${index}`} className="grid grid-cols-[1fr_100px_140px] gap-3 rounded-md border border-slate-800 bg-slate-950 p-3 text-sm">
                <span>{item.resource_type}</span>
                <span>{item.quantity}</span>
                <span className="text-slate-500">{item.source}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-2 text-sm text-slate-400">
            {Object.entries(usage).map(([resource, total]) => (
              <p key={resource}>{resource}: {total}</p>
            ))}
            <p>Select usage details for row-level provenance.</p>
          </div>
        )}
      </Panel>
    </div>
  );
}

function UsersTab({
  members,
  onInvite,
  onRoleChange,
  saving,
}: {
  members: any[];
  onInvite: () => void;
  onRoleChange: (member: any, role: string) => void;
  saving: string | null;
}) {
  return (
    <Panel title="Users & Roles" action={<Button onClick={onInvite} disabled={saving === 'invite'}>Invite User</Button>}>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">User</th>
              <th>Role</th>
              <th>Permissions</th>
              <th>Last Active</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.map((member: any) => (
              <tr key={`${member.id}-${member.email}`} className="border-t border-slate-800">
                <td className="py-3">
                  <p className="font-medium">{member.name}</p>
                  <p className="text-slate-500">{member.email}</p>
                </td>
                <td>
                  <select
                    value={member.role}
                    onChange={(event) => onRoleChange(member, event.target.value)}
                    className="rounded-md border border-slate-700 bg-slate-950 p-2 text-sm text-slate-100"
                  >
                    {roles.map((role) => <option key={role}>{role}</option>)}
                  </select>
                </td>
                <td>{(member.permissions || []).join(', ')}</td>
                <td>{new Date(member.last_active_at).toLocaleString()}</td>
                <td><Pill tone={member.status === 'active' ? 'green' : 'orange'}>{member.status}</Pill></td>
                <td><Pill>{member.id ? 'Editable' : 'Demo'}</Pill></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-sm text-slate-300">
      {label}
      <input
        value={value || ''}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none"
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="block text-sm text-slate-300">
      {label}
      <select
        value={value || options[0]}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none"
      >
        {options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </label>
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
      {quota?.provenance ? (
        <p className="mt-1 text-xs text-slate-500">
          {quota.provenance.source} / confidence {Math.round(quota.provenance.confidence * 100)}%
        </p>
      ) : null}
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
