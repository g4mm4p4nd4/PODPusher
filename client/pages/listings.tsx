import ListingComposer from '../components/ListingComposer';
import { useTranslation } from 'next-i18next';

export default function Listings() {
  const { t } = useTranslation('common');
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('listings.pageTitle')}</h1>
      <ListingComposer />
    </div>
  );
}
