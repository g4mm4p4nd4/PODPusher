import React, { useEffect, useState } from 'react';
import { useTranslation } from 'next-i18next';
import { getPreferences, savePreferences, Preferences } from '../services/userPreferences';

export default function SocialSettings() {
  const { t } = useTranslation('common');
  const [prefs, setPrefs] = useState<Preferences>({ auto_social: true, social_handles: {} });

  useEffect(() => {
    getPreferences().then(setPrefs).catch(console.error);
  }, []);

  const updateHandle = (network: string, value: string) => {
    setPrefs({ ...prefs, social_handles: { ...prefs.social_handles, [network]: value } });
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    await savePreferences(prefs);
  };

  return (
    <form onSubmit={save} className="space-y-4" aria-label={t('settings.title')}>
      <h1 className="text-2xl font-bold">{t('settings.title')}</h1>
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={prefs.auto_social}
          onChange={(e) => setPrefs({ ...prefs, auto_social: e.target.checked })}
        />
        <span>{t('settings.auto')}</span>
      </label>
      <input
        className="border p-2 w-full"
        placeholder={t('settings.instagram')}
        value={prefs.social_handles.instagram || ''}
        onChange={(e) => updateHandle('instagram', e.target.value)}
      />
      <input
        className="border p-2 w-full"
        placeholder={t('settings.facebook')}
        value={prefs.social_handles.facebook || ''}
        onChange={(e) => updateHandle('facebook', e.target.value)}
      />
      <input
        className="border p-2 w-full"
        placeholder={t('settings.twitter')}
        value={prefs.social_handles.twitter || ''}
        onChange={(e) => updateHandle('twitter', e.target.value)}
      />
      <button type="submit" className="px-4 py-2 bg-blue-600 text-white">
        {t('settings.save')}
      </button>
    </form>
  );
}
