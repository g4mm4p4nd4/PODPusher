import fs from 'fs';
import path from 'path';
import type { GetStaticProps } from 'next';
import type { UserConfig } from 'next-i18next';
import nextI18NextConfig from '../next-i18next.config';

type NamespaceStore = Record<string, unknown>;

type I18nProps = {
  _nextI18Next: {
    initialI18nStore: Record<string, Record<string, NamespaceStore>>;
    initialLocale: string;
    ns: string[];
    userConfig: UserConfig;
  };
};

function loadNamespace(locale: string, namespace: string): NamespaceStore {
  const configuredLocalePath = (nextI18NextConfig as UserConfig).localePath;
  const localePath = typeof configuredLocalePath === 'string'
    ? configuredLocalePath
    : path.resolve(process.cwd(), 'locales');
  const filePath = path.join(localePath, locale, `${namespace}.json`);
  return JSON.parse(fs.readFileSync(filePath, 'utf-8')) as NamespaceStore;
}

function buildCommonI18nProps(locale?: string): I18nProps {
  const initialLocale = locale ?? 'en';
  const namespaces = ['common'];
  const locales = Array.from(new Set([initialLocale, 'en']));
  const initialI18nStore: Record<string, Record<string, NamespaceStore>> = {};

  for (const currentLocale of locales) {
    initialI18nStore[currentLocale] = {};
    for (const namespace of namespaces) {
      try {
        initialI18nStore[currentLocale][namespace] = loadNamespace(currentLocale, namespace);
      } catch {
        initialI18nStore[currentLocale][namespace] = loadNamespace('en', namespace);
      }
    }
  }

  return {
    _nextI18Next: {
      initialI18nStore,
      initialLocale,
      ns: namespaces,
      userConfig: nextI18NextConfig as UserConfig,
    },
  };
}

export async function getCommonServerSideProps(locale?: string) {
  return buildCommonI18nProps(locale);
}

export const getCommonStaticProps: GetStaticProps = async ({ locale }) => ({
  props: buildCommonI18nProps(locale),
});
