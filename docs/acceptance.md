# Acceptance boundaries — reconstruction 2

Local checks cover actual production RaceClient modules and render adapters in two independent Node processes against a separate authority: same start/epoch/results, both cars moving, reconnect same seat and continuing clock, no token disclosure through production events, rematch, malformed/regressive state and exact endpoint/build gates.

Stable V11.1 engine anchors and world/collider bytes match. Full mutable driver state is compared to separate direct stable GameModels. Stock reverse is tested on road/shoulder/deep grass with -15%, flat and +15% grades. Blocked-water recovery retries are server-clock bounded and do not invent success. Baseline handling/recovery and reverse/obstacle tests are retained.

Actual GLTFLoader and Three scene-graph tests exercise fixed car slots, exactly two visible human seats, wheels/steer/ground normals, camera/checkpoint transforms, complete runtime assets and no traffic/police/coin rendering. Water geometry is compared against21,229 actual GLB CPU raycasts. These are not screenshots or WebGL/GPU acceptance.

Solo-profile regression throws on any localStorage access and verifies a later seven-car/currency sentinel is untouched. Only the online session key may be written. No profile normalization, migration or payout is invoked.

Authority/hosting tests retain input/version/room/host permissions, rejoin-token rotation, stale braking, expired-seat DNF, control-frame/transport quotas, static path/size/hash/no-symlink restrictions, bounded concurrency/bytes, exact CSP and no backend fallback.

**Pending, not claimed:** current-browser DOM/layout/accessibility, real WebGL/GPU, desktop/mobile performance, physical keyboard/touch/human driving, adverse internet conditions/cold-start UX, exact endpoint activation and remote HTTP/WSS/two-human acceptance. Earlier Chromium probe in the prior executor was blocked before page load; that does not establish current-browser acceptance. No sandbox bypass is used.

This activation candidate approves only `https://kerala-roadster-multiplayer-alpha.onrender.com`; all other public origins remain disabled. Initial disabled deployment and activation deployment require separate exact-revision verification. Owner licence decision remains pending. This standalone alpha does not overwrite or migrate solo V12.

## Runtime patch after live timing failure

The second actual public two-process attempt acknowledged23 inputs per car and moved both to s2209.54 before the250ms fail-safe ended both DNF/server-overload at elapsed0.75s. The first attempt lacked retained diagnostics; its exact reason is unknown. Local cold/warm profiling supports JIT warmup as a hypothesis, not proof of the provider cause. This patch keeps the guard unchanged, warms a discarded600-tick world before listening and emits bounded aggregate timing/CPU diagnostics.

Current tests:17 client/joint/origin/asset tests,23 authority/hosting/runtime tests,175 handling/recovery,27 reverse cases across30/60/120Hz,66 obstacle approaches/54 contacted reverse escapes, and21,229 water raycasts pass. The exact production entrypoint passes npm production-only install/root/health smoke. Online asset loading requests no coin; all other selectedGLBs have no images. Solo renderer default and physics/assets/pins are unchanged.

Cloud Chrome reached the live document, but WebGL context creation failed before asset loading (graphics disabled); the UI correctly disables entry and reports WebGL2 unavailable. This is an environment blocker, not GPU acceptance or a reproduced coin-CSP violation. Runtime patch internet effectiveness, visual/keyboard/touch/human tests remain pending.
