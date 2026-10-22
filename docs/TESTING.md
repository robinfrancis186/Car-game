# Verification scope

```sh
npm ci --ignore-scripts --omit=dev
npm test
npm run test:regression
```

The reviewed 22 October 2026 public-alpha freeze passed **15/15** network/security/world tests and **128/128** unchanged V10 pure-JavaScript gameplay regression tests. Publication reruns use an isolated copy of the same runtime/test files.

Coverage includes independent server/client processes, common authoritative start/results, input/schema/version rejection, equal stock/noncontact world contexts, authored water queries, reconnect rotation/expiry, room/readiness/host permissions, fail-closed Render configuration, exact Host/Origin rejection, quotas/backpressure, control-frame floods, expired-host repair and graceful shutdown.

Internal review reports, process IDs, local paths and run-specific logs are not distributed. Tests regenerate ignored local evidence under `docs/`. These records are automation evidence only—not proof of real internet play, human handling, audible sound, mobile/GPU performance or integrated 3D multiplayer. Public availability and remote TLS/WSS require separate deployment acceptance.

Optional water tools accept a separate checkout of V10 from `main`: install its `web/` dependencies, then pass that checkout's `web` directory to `tools/verify_water_raycast.mjs`. The server and normal tests need no GLB renderer or Blender installation.
