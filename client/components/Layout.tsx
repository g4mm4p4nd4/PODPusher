import Link from 'next/link';
import { ReactNode, useEffect, useState } from 'react';
import axios from 'axios';

export default function Layout({ children }: { children: ReactNode }) {
  const [usage, setUsage] = useState<{ plan: string; images_used: number; limit: number } | null>(null);
  const api = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    axios
      .get(`${api}/user/plan`, { headers: { 'X-User-Id': '1' } })
      .then((res) => setUsage(res.data))
      .catch((err) => console.error(err));
  }, [api]);

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-gray-800 text-white p-4">
        <div className="container mx-auto flex gap-4 items-center">
          <Link href="/" className="hover:underline">Home</Link>
          <Link href="/generate" className="hover:underline">Generate</Link>
          <Link href="/categories" className="hover:underline">Categories</Link>
          <Link href="/design" className="hover:underline">Design Ideas</Link>
          <Link href="/suggestions" className="hover:underline">Suggestions</Link>
          <Link href="/analytics" className="hover:underline">Analytics</Link>
          <span className="ml-auto text-sm" data-testid="quota">
            {usage ? `${usage.images_used}/${usage.limit} images` : ''}
          </span>
        </div>
      </nav>
      <main className="flex-1 container mx-auto p-4">{children}</main>
    </div>
  );
}
