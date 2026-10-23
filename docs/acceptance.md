# Acceptance boundaries — protocol 3 interruption candidate

Local checks cover actual production RaceClient modules and render adapters in two independent Node processes against a separate authority: same start/epoch/results, both cars moving, reconnect same seat and continuing clock, no token disclosure through production events, rematch, malformed/regressive state and exact endpoint/build gates.

Stable V11.1 engine anchors and world/collider bytes match. Full mutable driver state is compared to separate direct stable GameModels. Stock reverse is tested on road/shoulder/deep grass with -15%, flat and +15% grades. Blocked-water recovery retries are server-clock bounded and do not invent success. Baseline handling/recovery and reverse/obstacle tests are retained.

Actual GLTFLoader and Three scene-graph tests exercise fixed car slots, exactly two visible human seats, wheels/steer/ground normals, camera/checkpoint transforms, complete runtime assets and no traffic/police/coin rendering. Water geometry is compared against21,229 actual GLB CPU raycasts. These are not screenshots or WebGL/GPU acceptance.

Solo-profile regression throws on any localStorage access and verifies a later seven-car/currency sentinel is untouched. Only the online session key may be written. No profile normalization, migration or payout is invoked.

Authority/hosting tests retain input/version/room/host permissions, rejoin-token rotation, stale braking, expired-seat DNF, control-frame/transport quotas, static path/size/hash/no-symlink restrictions, bounded concurrency/bytes, exact CSP and no backend fallback.

**Pending, not claimed:** current-browser DOM/layout/accessibility, real WebGL/GPU, desktop/mobile performance, physical keyboard/touch/human driving, adverse internet conditions/cold-start UX, exact endpoint activation and remote HTTP/WSS/two-human acceptance. Earlier Chromium probe in the prior executor was blocked before page load; that does not establish current-browser acceptance. No sandbox bypass is used.

This activation candidate approves only `https://kerala-roadster-multiplayer-alpha.onrender.com`; all other public origins remain disabled. Initial disabled deployment and activation deployment require separate exact-revision verification. Owner licence decision remains pending. This standalone alpha does not overwrite or migrate solo V12.

## Historical protocol-2 runtime patch after live timing failure

The second actual public two-process attempt acknowledged23 inputs per car and moved both to s2209.54 before the250ms fail-safe ended both DNF/server-overload at elapsed0.75s. The first attempt lacked retained diagnostics; its exact reason is unknown. Local cold/warm profiling supports JIT warmup as a hypothesis, not proof of the provider cause. This patch keeps the guard unchanged, warms a discarded600-tick world before listening and emits bounded aggregate timing/CPU diagnostics.

Current tests:17 client/joint/origin/asset tests,23 authority/hosting/runtime tests,175 handling/recovery,27 reverse cases across30/60/120Hz,66 obstacle approaches/54 contacted reverse escapes, and21,229 water raycasts pass. The exact production entrypoint passes npm production-only install/root/health smoke. Online asset loading requests no coin; all other selectedGLBs have no images. Solo renderer default and physics/assets/pins are unchanged.

Cloud Chrome reached the live document, but WebGL context creation failed before asset loading (graphics disabled); the UI correctly disables entry and reports WebGL2 unavailable. This is an environment blocker, not GPU acceptance or a reproduced coin-CSP violation. Runtime patch internet effectiveness, visual/keyboard/touch/human tests remain pending.

## Historical protocol-2 reconnect watchdog patch

A full public no-disconnect baseline on6ad43ec4 finished both cars with10checkpoints in91.558/92.033seconds, identical results and rematch reset. A separate forced-disconnect run expired without rejoining. Local red tests reproduce a client scheduling defect: when the old attempt is already older than5seconds, the250ms watchdog treats socket-free retry backoff as an active handshake, perpetually resetting the600ms retry.

The only runtime source change adds a pending-socket guard. Red2fail/green2pass regressions verify retry after an aged disconnect, retry after a5second handshake timeout, and the unchanged original20second deadline. The independent-process local lifecycle test waits an additional5200ms after movement before disconnect; same-seat/clock/results/rematch pass. Full tests now19client/joint/asset/origin/reconnect plus23authority/hosting/runtime, with all prior physics/water baselines passing. No server/asset/physics/CSP/timeout/security or solo-save changes. New exact deploy and public reconnect validation are still required; browser/GPU/human acceptance remains separate.

## Current protocol-3 bounded interruption candidate

The actual live reconnect patch subsequently reported a 484.364 ms loop gap, 492.734 ms backlog and 1.631 ms process CPU in that sample, with last step 6.282 ms. This establishes a blocked/scheduled-away interval, not its exact provider cause. The observed free quota is 0.15 CPU core. No paid upgrade, relaxed origin/quota, hidden catchup or invented success is used.

New version-pinned rule: detect backlog over 250 ms; freeze both authoritative cars/clock/checkpoints/recovery/energy, discard backlog, clear controls and interpolation, hold for 500 ms stable scheduling. Generation changes at both hold start and end, rejecting pre-hold and queued during-hold commands. Bound each interruption to 2 s, at most 3 events, at most 5 s aggregate; charge lost gap plus stable hold. Exceeding a bound ends unfinished seats as server-interrupted DNF while preserving actual finishes. Only a legitimate rematch resets the budget. A player cannot request a hold; the existing 20 s wall reconnect window remains unchanged.

Local tests inject a 484 ms stall into a separate authority and use the actual RaceClient/adapter in two independent client processes: identical freeze/resume poses/clock, continued movement, aged automatic reconnect, both finished results and rematch. Additional authority tests cover high-CPU stalls, repeated gaps, exact cap boundaries, fourth event, held reconnect/token rotation, wall expiry and preserving a real finish. Client tests cover old/malformed/regressive state, strict generation fencing, accessible banner markup, wheel/interpolation freeze and no solo-storage writes.

The visible banner reports server-confirmed duration (not a fabricated live clock); final interrupted duration is separate from timed race results. Existing no-player-pause wording is explicitly distinguished from automatic host interruption. Browser rendering/accessibility/human control acceptance is still unverified because the cloud browser has no WebGL context. New protocol-3 public full race, reconnect and interruption behavior require exact deployment acceptance. A local benchmark is not a guarantee under the provider's 0.15-core quota. See the current patch receipt for exact tested totals.
