import { useTranslation } from 'next-i18next';
import { serverSideTranslations } from 'next-i18next/serverSideTranslations';
import { GetStaticProps } from 'next';
import OAuthConnect from '../components/OAuthConnect';
import SocialSettings from '../components/SocialSettings';
import UserQuota from '../components/UserQuota';

export default function SettingsPage() {
  const { t } = useTranslation('common');

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">
        {t('settings.pageTitle', 'Settings')}
      </h1>

      {/* Connected Accounts Section */}
      <section className="bg-white rounded-lg shadow p-6">
        <OAuthConnect />
      </section>

      {/* Quota Section */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">
          {t('settings.usageQuota', 'Usage & Quota')}
        </h2>
        <UserQuota />
      </section>

      {/* Social Media Settings Section */}
      <section className="bg-white rounded-lg shadow p-6">
        <SocialSettings />
      </section>
    </div>
  );
}

export const getStaticProps: GetStaticProps = async ({ locale }) => {
  return {
    props: {
      ...(await serverSideTranslations(locale ?? 'en', ['common'])),
    },
  };
};
