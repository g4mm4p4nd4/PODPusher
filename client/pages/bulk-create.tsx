import BulkUploader from '../components/BulkUploader';
import { useTranslation } from 'next-i18next';

export default function BulkCreate() {
  const { t } = useTranslation('common');
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t('bulk.title')}</h1>
      <BulkUploader />
    </div>
  );
}
