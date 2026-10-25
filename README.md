# MALABAR — Hot Coast · V17 R3.4

Play: **https://malabar-hot-coast.vercel.app/**

This repository contains the exact R3.4 browser game currently published on Vercel, its original editable Blender scenes, generators, tests and asset/license documentation. R3.4 unifies the desktop/mobile orange-dark interface, removes duplicate menu routes, fixes bounded HUD/dock overlap and adds **Leaderboard — On this device**. Leaderboard names and records stay in the current browser/origin; there is no global online leaderboard. Existing cars, credits and Story saves are preserved.

## Run and build

Requires Node.js 20+ and Python 3; driving requires a WebGL2 browser.

```sh
cd web
npm ci --ignore-scripts --no-audit --no-fund
npm test
npm run build
python3 ../tools/verify-standalone.py
npm run serve
```

Open http://localhost:8080. `npm run build` creates the self-contained `dist/malabar-hot-coast.html` with original assets and third-party notices embedded. To reproduce the exact 151-file static production package:

```sh
node tools/build-static.mjs
python3 tools/verify-publication.py
```

The output is `dist/vercel/`. Generated distributions, dependencies, private reference media and caches are intentionally not committed.

## Verification and limits

`deployment/production-verification.json` records a fresh HTTP/SHA-256 comparison of all 151 published files. `SOURCE_MANIFEST.json` connects the 147 frozen runtime files to the READY production deployment. `ASSET_SOURCE_MANIFEST.json` inventories all 45 editable native asset scenes. Read `TESTING.md`, `AUTHORING.md`, `PROVENANCE.md` and `LICENSES.md` for scope.

The exact artifact passed bounded native desktop/mobile menu checks and automated controller/model checks. This is a solo arcade prototype: actual completed-race name persistence, GPU-loss/restore, performance, listening and mobile-driving acceptance are not all natively verified. Historical documents retain their original stage-specific caveats and are not the current release status.

No new blanket reuse license is granted by publication. Preserve third-party licenses, OpenStreetMap attribution and prior scoped notices.
