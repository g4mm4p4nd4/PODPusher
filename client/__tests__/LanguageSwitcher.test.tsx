import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import Layout from '../components/Layout';

jest.mock('../components/QuotaDisplay', () => () => <span />);
jest.mock('axios', () => ({ get: jest.fn().mockResolvedValue({ data: [] }) }));

const resources = {
  en: { common: { nav: {
    home: 'Home', generate: 'Generate', categories: 'Categories', designIdeas: 'Design Ideas', suggestions: 'Suggestions', search: 'Search', analytics: 'Analytics', listings: 'Listings', abTests: 'A/B Tests', notifications: 'Notifications', socialGenerator: 'Social Generator', settings: 'Settings', searchPlaceholder: 'Search...'
  } } },
  es: { common: { nav: {
    home: 'Inicio', generate: 'Generar', categories: 'Categorías', designIdeas: 'Ideas de diseño', suggestions: 'Sugerencias', search: 'Buscar', analytics: 'Analíticas', listings: 'Publicaciones', abTests: 'Pruebas A/B', notifications: 'Notificaciones', socialGenerator: 'Generador Social', settings: 'Configuración', searchPlaceholder: 'Buscar...'
  } } },
};

i18n.use(initReactI18next).init({ resources, lng: 'en', fallbackLng: 'en', interpolation: { escapeValue: false } });

const router: any = {
  locale: 'en',
  locales: ['en', 'es'],
  pathname: '/',
  query: {},
  asPath: '/',
  push: jest.fn((path: any, as: any, opts: any) => {
    router.locale = opts.locale;
    i18n.changeLanguage(opts.locale);
  }),
  replace: jest.fn(),
};

jest.mock('next/router', () => ({
  useRouter: () => router,
}));

test('toggling language switcher updates nav text', () => {
  render(<Layout><div /></Layout>);
  expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument();
  fireEvent.change(screen.getByTestId('language-switcher'), { target: { value: 'es' } });
  expect(router.push).toHaveBeenCalled();
  expect(screen.getByRole('link', { name: 'Inicio' })).toBeInTheDocument();
});
