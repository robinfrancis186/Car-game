# V17 R3.6 Git-to-production handoff

Deployment ownership belongs to the parent task. This executor does not deploy. Canonical target: `malabar-hot-coast`, project `prj_wpjGOHOOw8yWEFnoKJeBe8ZTu6d5`, https://malabar-hot-coast.vercel.app/ .

From the final pushed commit, run `node tools/build-static.mjs` and publish only `dist/vercel`. `deployment/runtime-manifest.json` maps every output path to its committed source bytes and SHA-256; it can also drive connector-based static uploads without running a build. Never upload the repository root, authoring/reference files, `.git`, `.vercel`, local deliveries or private photos.

The exact prior R3.5 receipts are retained under `deployment/history/r3-5/`. Keep deployment `dpl_4w3s2tzYtKpaJMrdL6dvbx7iEmkD` for rollback. Root `production-verification.json` still describes R3.5 and must not be read as proof of R3.6 deployment. After publishing, verify the live `release.json` and all mapped public files, then record the actual commit/deployment IDs and results. No project/account/security settings need changing.

Validation and limitations are in `deployment/publication-checks.json`, the native metadata-only audit, and `assets/capture_humans/README.md`. The gameplay/media bytes match the validated candidate; publication additions are licence/release metadata and path-sanitized native copies.
