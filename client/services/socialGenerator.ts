import axios from 'axios';

export interface SocialPost {
  caption: string;
  image_url: string;
}

export async function generateSocialPost(prompt: string): Promise<SocialPost> {
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const res = await axios.post<SocialPost>(`${api}/social/post`, { prompt });
  return res.data;
}
