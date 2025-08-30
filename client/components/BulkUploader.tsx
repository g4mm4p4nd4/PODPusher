import axios from 'axios';
import React, { useState } from 'react';
import { useTranslation } from 'next-i18next';

export default function BulkUploader() {
  const { t } = useTranslation('common');
  const [progress, setProgress] = useState(0);
  const [summary, setSummary] = useState<any | null>(null);
  const [errorLink, setErrorLink] = useState<string | null>(null);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const upload = async (file: File) => {
    const form = new FormData();
    form.append('file', file);
    setProgress(1);
    try {
      const res = await axios.post(`${api}/api/bulk_create`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) {
            setProgress(Math.round((e.loaded / e.total) * 50));
          }
        },
      });
      setProgress(100);
      setSummary(res.data);
      if (res.data.errors && res.data.errors.length) {
        const csv =
          'row,error\n' +
          res.data.errors.map((e: any) => `${e.row},${e.error}`).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        setErrorLink(URL.createObjectURL(blob));
      }
    } catch (err) {
      setProgress(0);
    }
  };

  const handleFiles = (files: FileList) => {
    if (files && files.length) {
      upload(files[0]);
    }
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length) {
      upload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
      className="border-dashed border-2 p-8 text-center"
    >
      <p>{t('bulk.upload')}</p>
      <input
        type="file"
        accept=".csv,application/json"
        onChange={(e) => handleFiles(e.target.files as FileList)}
        className="my-4"
      />
      {progress > 0 && (
        <div>
          <p>{t('bulk.progress')}</p>
          <progress value={progress} max={100} />
        </div>
      )}
      {summary && (
        <div className="mt-4">
          <p>{summary.created.length} {t('bulk.created')}</p>
          {summary.errors.length > 0 && (
            <div>
              <p>{t('bulk.errors')}</p>
              <table className="table-auto border mt-2">
                <thead>
                  <tr>
                    <th className="border px-2">Row</th>
                    <th className="border px-2">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.errors.map((e: any) => (
                    <tr key={e.row}>
                      <td className="border px-2">{e.row}</td>
                      <td className="border px-2">{e.error}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {errorLink && (
                <a
                  href={errorLink}
                  download="errors.csv"
                  className="text-blue-500"
                >
                  {t('bulk.download')}
                </a>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
