import axios from 'axios';
import { resolveApiUrl } from './apiBase';

export async function uploadBulk(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await axios.post(resolveApiUrl('/api/bulk_create'), form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data as { created: any[]; errors: any[] };
}
