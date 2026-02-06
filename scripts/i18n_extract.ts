#!/usr/bin/env ts-node
/**
 * i18n String Extraction Script
 *
 * Scans client/pages and client/components for hard-coded user-facing strings
 * that are not wrapped in translation calls (t() or useTranslation).
 * Outputs missing keys to stdout as JSON.
 *
 * Usage:
 *   npx ts-node scripts/i18n_extract.ts
 *   npm run i18n:extract
 *
 * Owner: Frontend-Coder (per DEVELOPMENT_PLAN.md Task 1.1.2)
 */

import * as fs from 'fs';
import * as path from 'path';

const CLIENT_DIR = path.resolve(__dirname, '..', 'client');
const LOCALES_DIR = path.join(CLIENT_DIR, 'locales');
const PAGES_DIR = path.join(CLIENT_DIR, 'pages');
const COMPONENTS_DIR = path.join(CLIENT_DIR, 'components');

interface MissingKey {
  file: string;
  line: number;
  text: string;
  suggestedKey: string;
}

function loadLocaleKeys(locale: string): Set<string> {
  const filePath = path.join(LOCALES_DIR, locale, 'common.json');
  if (!fs.existsSync(filePath)) {
    console.error(`Locale file not found: ${filePath}`);
    return new Set();
  }
  const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  const keys = new Set<string>();

  function walk(obj: Record<string, unknown>, prefix: string) {
    for (const [key, value] of Object.entries(obj)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;
      if (typeof value === 'object' && value !== null) {
        walk(value as Record<string, unknown>, fullKey);
      } else {
        keys.add(fullKey);
      }
    }
  }

  walk(data, '');
  return keys;
}

function findHardCodedStrings(filePath: string): MissingKey[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const results: MissingKey[] = [];

  // Patterns that indicate a hard-coded user-facing string in JSX
  // Look for string literals inside JSX (between > and <)
  const jsxTextPattern = />\s*([A-Z][a-zA-Z\s]{2,})\s*</g;
  // Look for string props like placeholder="..." title="..." label="..."
  const propPattern = /(?:placeholder|title|label|aria-label)="([A-Z][a-zA-Z\s]{2,})"/g;

  const relativePath = path.relative(CLIENT_DIR, filePath);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Skip import lines, comments, and lines already using t()
    if (
      line.trim().startsWith('import') ||
      line.trim().startsWith('//') ||
      line.trim().startsWith('*') ||
      line.includes("t('") ||
      line.includes('t("') ||
      line.includes('t(`')
    ) {
      continue;
    }

    let match;
    jsxTextPattern.lastIndex = 0;
    while ((match = jsxTextPattern.exec(line)) !== null) {
      const text = match[1].trim();
      if (text.length > 2 && !/^[A-Z_]+$/.test(text)) {
        results.push({
          file: relativePath,
          line: i + 1,
          text,
          suggestedKey: generateKey(relativePath, text),
        });
      }
    }

    propPattern.lastIndex = 0;
    while ((match = propPattern.exec(line)) !== null) {
      const text = match[1].trim();
      if (text.length > 2) {
        results.push({
          file: relativePath,
          line: i + 1,
          text,
          suggestedKey: generateKey(relativePath, text),
        });
      }
    }
  }

  return results;
}

function generateKey(filePath: string, text: string): string {
  const pageName = path
    .basename(filePath, path.extname(filePath))
    .replace(/[^a-zA-Z]/g, '_');
  const slug = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 30);
  return `${pageName}.${slug}`;
}

function scanDirectory(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  const files: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...scanDirectory(fullPath));
    } else if (/\.(tsx?|jsx?)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
  return files;
}

function compareLocales(baseLocale: string, targetLocale: string): string[] {
  const baseKeys = loadLocaleKeys(baseLocale);
  const targetKeys = loadLocaleKeys(targetLocale);
  const missing: string[] = [];

  for (const key of baseKeys) {
    if (!targetKeys.has(key)) {
      missing.push(key);
    }
  }

  return missing;
}

// Main execution
const enKeys = loadLocaleKeys('en');
console.log(`English locale has ${enKeys.size} keys\n`);

// Check locale parity
for (const locale of ['es', 'fr', 'de']) {
  const missing = compareLocales('en', locale);
  if (missing.length > 0) {
    console.log(`Missing keys in '${locale}' locale (${missing.length}):`);
    missing.forEach((k) => console.log(`  - ${k}`));
    console.log();
  } else {
    console.log(`Locale '${locale}': all keys present`);
  }
}

// Scan for hard-coded strings
const allFiles = [...scanDirectory(PAGES_DIR), ...scanDirectory(COMPONENTS_DIR)];
const allMissing: MissingKey[] = [];

for (const file of allFiles) {
  allMissing.push(...findHardCodedStrings(file));
}

if (allMissing.length > 0) {
  console.log(`\nPotential hard-coded strings found (${allMissing.length}):`);
  console.log(JSON.stringify(allMissing, null, 2));
} else {
  console.log('\nNo hard-coded strings detected.');
}

process.exit(allMissing.length > 0 ? 1 : 0);
