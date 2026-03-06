import { test, expect, type Page } from '@playwright/test';

const BASE_PREFS = {
  auto_social: true,
  social_handles: {},
  email_notifications: true,
  push_notifications: false,
  preferred_language: 'en',
  preferred_currency: 'USD',
  timezone: 'UTC',
};

async function mockLayoutApis(page: Page) {
  await page.route('**/api/notifications**', async (route) => {
    if (route.request().method() === 'PUT') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({}),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });
}

async function mockSettingsApis(page: Page, overrides: Partial<typeof BASE_PREFS> = {}) {
  await mockLayoutApis(page);

  let prefs = { ...BASE_PREFS, ...overrides };

  await page.route('**/api/user/preferences', async (route) => {
    if (route.request().method() === 'POST') {
      const payload = route.request().postDataJSON() as Partial<typeof BASE_PREFS>;
      prefs = { ...prefs, ...payload };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(prefs),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(prefs),
    });
  });

  await page.route('**/api/auth/providers', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });

  await page.route('**/api/auth/credentials', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });
}

function settingsCurrencySelect(page: Page) {
  return page.locator('form[aria-label]').locator('select').nth(1);
}

test.describe('Language Switcher', () => {
  test.beforeEach(async ({ page }) => {
    await mockLayoutApis(page);
  });

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
    await expect(page.getByRole('link', { name: /G.n.rer/ })).toBeVisible();
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
    await mockLayoutApis(page);
    await mockSettingsApis(page, { preferred_language: 'es', preferred_currency: 'EUR' });
    await page.goto('/');
    await page.getByTestId('language-switcher').selectOption('es');
  });

  test('analytics page uses translated strings', async ({ page }) => {
    await page.goto('/es/analytics');
    await expect(page.getByRole('heading', { name: /Panel de Anal.tica/ })).toBeVisible();
  });

  test('notifications page uses translated strings', async ({ page }) => {
    await page.goto('/es/notifications');
    await expect(page.locator('main h1')).toHaveText('Notificaciones');
  });

  test('settings page uses translated strings', async ({ page }) => {
    await page.goto('/es/settings');
    await expect(page.locator('main > div > h1').first()).toHaveText(/Configuraci.n/);
  });
});

test.describe('Page Translations - French', () => {
  test.beforeEach(async ({ page }) => {
    await mockSettingsApis(page, { preferred_language: 'fr', preferred_currency: 'EUR' });
  });

  test('analytics page uses French strings', async ({ page }) => {
    await page.goto('/fr/analytics');
    await expect(page.getByRole('heading', { name: 'Tableau de bord analytique' })).toBeVisible();
  });

  test('settings page uses French strings', async ({ page }) => {
    await page.goto('/fr/settings');
    await expect(page.locator('main > div > h1').first()).toHaveText(/Param.tres/);
  });

  test('notifications page uses French strings', async ({ page }) => {
    await page.goto('/fr/notifications');
    await expect(page.locator('main h1')).toHaveText('Notifications');
  });
});

test.describe('Page Translations - German', () => {
  test.beforeEach(async ({ page }) => {
    await mockSettingsApis(page, { preferred_language: 'de', preferred_currency: 'EUR' });
  });

  test('analytics page uses German strings', async ({ page }) => {
    await page.goto('/de/analytics');
    await expect(page.getByRole('heading', { name: 'Analytik-Dashboard' })).toBeVisible();
  });

  test('settings page uses German strings', async ({ page }) => {
    await page.goto('/de/settings');
    await expect(page.locator('main > div > h1').first()).toHaveText('Einstellungen');
  });

  test('notifications page uses German strings', async ({ page }) => {
    await page.goto('/de/notifications');
    await expect(page.locator('main h1')).toHaveText('Benachrichtigungen');
  });
});

test.describe('Settings Preferences', () => {
  test('shows USD as the saved currency in English settings', async ({ page }) => {
    await mockSettingsApis(page, { preferred_currency: 'USD' });
    await page.goto('/settings');
    await expect(settingsCurrencySelect(page)).toHaveValue('USD');
  });

  test('allows selecting EUR in French settings', async ({ page }) => {
    await mockSettingsApis(page, { preferred_language: 'fr', preferred_currency: 'EUR' });
    await page.goto('/fr/settings');
    await expect(settingsCurrencySelect(page)).toHaveValue('EUR');
  });

  test('allows selecting EUR in German settings', async ({ page }) => {
    await mockSettingsApis(page, { preferred_language: 'de', preferred_currency: 'EUR' });
    await page.goto('/de/settings');
    await expect(settingsCurrencySelect(page)).toHaveValue('EUR');
  });

  test('persists a GBP selection after saving', async ({ page }) => {
    await mockSettingsApis(page, { preferred_currency: 'USD' });
    await page.goto('/settings');
    await settingsCurrencySelect(page).selectOption('GBP');
    await page.getByRole('button', { name: 'Save' }).click();
    await page.goto('/settings');
    await expect(settingsCurrencySelect(page)).toHaveValue('GBP');
  });

  test('persists a CAD selection across page navigation', async ({ page }) => {
    await mockSettingsApis(page, { preferred_currency: 'USD' });
    await page.goto('/settings');
    await settingsCurrencySelect(page).selectOption('CAD');
    await page.getByRole('button', { name: 'Save' }).click();
    await page.goto('/');
    await page.goto('/settings');
    await expect(settingsCurrencySelect(page)).toHaveValue('CAD');
  });

  test('uses EUR as the saved currency for Spanish settings', async ({ page }) => {
    await mockSettingsApis(page, { preferred_language: 'es', preferred_currency: 'EUR' });
    await page.goto('/es/settings');
    await expect(settingsCurrencySelect(page)).toHaveValue('EUR');
  });
});
