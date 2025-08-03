import React, { useEffect } from 'react';
import type { AppProps } from 'next/app';
import { appWithTranslation } from 'next-i18next';
import { useRouter } from 'next/router';
import '../styles/globals.css';
import Layout from '../components/Layout';
import { logEvent } from '../services/analytics';

export function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter();

  useEffect(() => {
    const handleRoute = (url: string) => {
      void logEvent('page_view', url);
    };
    handleRoute(router.asPath);
    router.events.on('routeChangeComplete', handleRoute);
    return () => {
      router.events.off('routeChangeComplete', handleRoute);
    };
  }, [router]);

  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  );
}

export default appWithTranslation(MyApp);
