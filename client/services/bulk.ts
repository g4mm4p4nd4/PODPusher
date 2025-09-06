import axios from 'axios';

const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function uploadBulk(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await axios.post(`${api}/api/bulk_create`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data as { created: any[]; errors: any[] };
}
