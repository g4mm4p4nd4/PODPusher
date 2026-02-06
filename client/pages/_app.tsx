import type { AppProps } from 'next/app';
import { appWithTranslation } from 'next-i18next';
import '../styles/globals.css';
import Layout from '../components/Layout';
import { ProviderProvider } from '../contexts/ProviderContext';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ProviderProvider>
      <Layout>
        <Component {...pageProps} />
      </Layout>
    </ProviderProvider>
  );
}

export default appWithTranslation(MyApp);
