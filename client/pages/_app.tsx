import type { AppProps } from 'next/app';
import { appWithTranslation } from 'next-i18next';
import type { UserConfig } from 'next-i18next';
import nextI18NextConfig from '../i18n.shared';
import '../styles/globals.css';
import Layout from '../components/Layout';
import ErrorBoundary from '../components/ErrorBoundary';
import { ProviderProvider } from '../contexts/ProviderContext';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ErrorBoundary>
      <ProviderProvider>
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </ProviderProvider>
    </ErrorBoundary>
  );
}

export default appWithTranslation(MyApp, nextI18NextConfig as UserConfig);
