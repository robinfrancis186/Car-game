/** Reproduce the exact published split runtime, without deploying or changing settings. */
import { cp, copyFile, mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'dist/vercel');
await rm(out, { recursive: true, force: true });
await mkdir(path.join(out, 'licenses'), { recursive: true });
for (const name of ['src', 'public']) await cp(path.join(root, 'web', name), path.join(out, name), { recursive: true });
for (const [source, target] of [
  ['web/index.html', 'index.html'], ['LICENSES.md', 'LICENSES.md'],
  ['web/public/assets/fonts/OFL.txt', 'licenses/OFL.txt'],
  ['web/public/vendor/THREE_LICENSE.txt', 'licenses/THREE_LICENSE.txt'],
  ['deployment/release.json', 'release.json']
]) await copyFile(path.join(root, source), path.join(out, target));
console.log('Built exact static package: dist/vercel (no deployment performed).');
