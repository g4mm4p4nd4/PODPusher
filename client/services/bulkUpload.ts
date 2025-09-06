export interface BulkResult {
  created: number;
  errors: string[];
}

export async function bulkCreate(file: File): Promise<BulkResult> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/bulk_create', {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error('upload_failed');
  return res.json();
}
