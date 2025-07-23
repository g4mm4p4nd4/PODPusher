import Link from 'next/link';
import { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-gray-800 text-white p-4">
        <div className="container mx-auto flex gap-4">
          <Link href="/" className="hover:underline">Home</Link>
          <Link href="/generate" className="hover:underline">Generate</Link>
          <Link href="/categories" className="hover:underline">Categories</Link>
        </div>
      </nav>
      <main className="flex-1 container mx-auto p-4">{children}</main>
    </div>
  );
}
