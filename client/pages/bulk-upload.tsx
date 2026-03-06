import BulkUploader from '../components/BulkUploader';
import { getCommonStaticProps } from '../utils/translationProps';

export default function BulkUploadPage() {
  return (
    <div className="space-y-4">
      <BulkUploader />
    </div>
  );
}

export const getStaticProps = getCommonStaticProps;
