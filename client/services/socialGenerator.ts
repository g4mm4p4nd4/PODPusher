import axios from 'axios';

export interface SocialRequest {
  product_id?: number;
  title?: string;
  description?: string;
  tags?: string[];
  product_type?: string;
  language?: string;
  include_image?: boolean;
}

export interface SocialPost {
  caption: string;
  image?: string | null;
}

export async function generateSocialPost(payload: SocialRequest): Promise<SocialPost> {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const res = await axios.post<SocialPost>(`${api}/api/social/generate`, payload);
  return res.data;
}
