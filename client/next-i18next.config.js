const fs = require('fs');
const path = require('path');
const shared = require('./i18n.shared');

function findLocalePath(startDirs) {
  const relativeCandidates = ['locales', path.join('client', 'locales')];

  for (const startDir of startDirs) {
    let current = path.resolve(startDir);

    while (true) {
      for (const relativeCandidate of relativeCandidates) {
        const candidate = path.resolve(current, relativeCandidate);
        if (fs.existsSync(candidate)) {
          return candidate;
        }
      }

      const parent = path.dirname(current);
      if (parent === current) {
        break;
      }
      current = parent;
    }
  }

  return path.resolve(process.cwd(), 'locales');
}

const localePath = findLocalePath([process.cwd(), __dirname]);

module.exports = {
  ...shared,
  localePath,
};
