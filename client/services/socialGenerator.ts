import axios from 'axios';
import { resolveApiUrl } from './apiBase';

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
  const res = await axios.post<SocialPost>(resolveApiUrl('/api/social/generate'), payload);
  return res.data;
}
