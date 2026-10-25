# Testing and release identity

From `web/`, run `npm ci --ignore-scripts --no-audit --no-fund`, `npm test`, and `npm run build` with Node.js 20+. Then run `python3 tools/verify-standalone.py` from the repository root. The full test chain has 53 command stages covering routes, physics, collisions, vehicle upgrades, saves, Story, aircraft, airtime, surface geometry, rendering state, menu/controller behavior and the local leaderboard. Fixtures and frozen baselines required by the chain are committed.

The release evidence records 93 JavaScript syntax checks, exact verification of 106 embedded assets and all 138 protected baseline files. `node tools/build-static.mjs` reproduces the public split deployment; `python3 tools/verify-publication.py` checks all 151 production files and all 45 native source hashes.

Automated fixtures include synthetic renderer/DOM/audio implementations and do not imply GPU, listening or full human-driving acceptance. The exact R3.4 native menu review covered 1222×619 desktop and 390×844 mobile, menu/navigation/theme/dock clearance. Actual completed-race name persistence, actual GPU-loss/restore, performance, audio listening and mobile driving remain native-acceptance limits as recorded in `deployment/release.json`.

All 45 editable `.blend` files were opened read-only with Blender auto-execution disabled during publication privacy checks. No linked libraries, embedded scripts or private/secret metadata were found; source bytes were unchanged.

Historical QA documents describe their own snapshots. Generated metrics, logs, previews and distributions are excluded from Git. Re-running tests regenerates some of these local outputs.
