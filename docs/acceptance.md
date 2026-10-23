# Acceptance boundaries — reconstruction 2

Local checks cover actual production RaceClient modules and render adapters in two independent Node processes against a separate authority: same start/epoch/results, both cars moving, reconnect same seat and continuing clock, no token disclosure through production events, rematch, malformed/regressive state and exact endpoint/build gates.

Stable V11.1 engine anchors and world/collider bytes match. Full mutable driver state is compared to separate direct stable GameModels. Stock reverse is tested on road/shoulder/deep grass with -15%, flat and +15% grades. Blocked-water recovery retries are server-clock bounded and do not invent success. Baseline handling/recovery and reverse/obstacle tests are retained.

Actual GLTFLoader and Three scene-graph tests exercise fixed car slots, exactly two visible human seats, wheels/steer/ground normals, camera/checkpoint transforms, complete runtime assets and no traffic/police/coin rendering. Water geometry is compared against21,229 actual GLB CPU raycasts. These are not screenshots or WebGL/GPU acceptance.

Solo-profile regression throws on any localStorage access and verifies a later seven-car/currency sentinel is untouched. Only the online session key may be written. No profile normalization, migration or payout is invoked.

Authority/hosting tests retain input/version/room/host permissions, rejoin-token rotation, stale braking, expired-seat DNF, control-frame/transport quotas, static path/size/hash/no-symlink restrictions, bounded concurrency/bytes, exact CSP and no backend fallback.

**Pending, not claimed:** current-browser DOM/layout/accessibility, real WebGL/GPU, desktop/mobile performance, physical keyboard/touch/human driving, adverse internet conditions/cold-start UX, exact endpoint activation and remote HTTP/WSS/two-human acceptance. Earlier Chromium probe in the prior executor was blocked before page load; that does not establish current-browser acceptance. No sandbox bypass is used.

Initial approved production origins are empty. Owner licence decision remains pending. This standalone alpha does not overwrite or migrate solo V12.
