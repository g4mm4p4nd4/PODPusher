/**
 * E2E Tests: Localization & i18n
 *
 * Owner: QA-Automator (per DEVELOPMENT_PLAN.md Task 1.1.6)
 * Reference: FC §7, i18n_plan.md
 *
 * Tests all supported locales (EN, ES, FR, DE) across key pages.
 */
import { test, expect } from '@playwright/test';

test.describe('Language Switcher', () => {
  test('updates navigation text to Spanish', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('language-switcher').selectOption('es');
    await expect(page.getByRole('link', { name: 'Inicio' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Generar' })).toBeVisible();
  });

  test('updates navigation text to French', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('language-switcher').selectOption('fr');
    await expect(page.getByRole('link', { name: 'Accueil' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Générer' })).toBeVisible();
  });

  test('updates navigation text to German', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('language-switcher').selectOption('de');
    await expect(page.getByRole('link', { name: 'Startseite' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Generieren' })).toBeVisible();
  });
});

test.describe('Page Translations - Spanish', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('language-switcher').selectOption('es');
  });

  test('analytics page uses translated strings', async ({ page }) => {
    await page.goto('/es/analytics');
    await expect(page.getByText('Panel de Analítica')).toBeVisible();
  });

  test('notifications page uses translated strings', async ({ page }) => {
    await page.goto('/es/notifications');
    await expect(page.getByText('Notificaciones')).toBeVisible();
  });

  test('settings page uses translated strings', async ({ page }) => {
    await page.goto('/es/settings');
    await expect(page.getByText('Configuración')).toBeVisible();
  });
});

test.describe('Page Translations - French', () => {
  test('analytics page uses French strings', async ({ page }) => {
    await page.goto('/fr/analytics');
    await expect(page.getByText('Tableau de bord analytique')).toBeVisible();
  });

  test('settings page uses French strings', async ({ page }) => {
    await page.goto('/fr/settings');
    await expect(page.getByText('Paramètres')).toBeVisible();
  });

  test('notifications page uses French strings', async ({ page }) => {
    await page.goto('/fr/notifications');
    await expect(page.getByText('Notifications')).toBeVisible();
  });
});

test.describe('Page Translations - German', () => {
  test('analytics page uses German strings', async ({ page }) => {
    await page.goto('/de/analytics');
    await expect(page.getByText('Analytik-Dashboard')).toBeVisible();
  });

  test('settings page uses German strings', async ({ page }) => {
    await page.goto('/de/settings');
    await expect(page.getByText('Einstellungen')).toBeVisible();
  });

  test('notifications page uses German strings', async ({ page }) => {
    await page.goto('/de/notifications');
    await expect(page.getByText('Benachrichtigungen')).toBeVisible();
  });
});
