# Localization Guide

The frontend uses **next-i18next** for translations. Language files are stored under `client/locales/<lang>/common.json`.

## Adding a New Language
1. Duplicate the `en` folder and translate each key.
2. Add the new locale code to `locales` in `client/next-i18next.config.js`.
3. Restart the frontend and verify translations using the language switcher.

## Changing the Default Locale
Edit `defaultLocale` in `client/next-i18next.config.js`. The dashboard will load using this locale when a user first visits the site.
