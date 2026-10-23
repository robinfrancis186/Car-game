# Kerala Roadster — V11.1 joint multiplayer / startup diagnostics candidate

Actual Three.js client + authoritative two-driver WebSocket races. Not the old Canvas demo and not the seven-car solo app.

## Startup diagnostic patch — not a root-cause fix

The prior native-browser startup failure remains unexplained. This patch preserves a safe failure stage/code (and HTTP status when available) after cleanup instead of replacing it with Offline / Left room. It also prevents later asset progress from hiding the error. Diagnostics never include raw exceptions, response bodies, URLs, or session tokens. Create/Join remain disabled after failure; validation, graphics requirements, CSP, physics, server timing rules, and all existing deadlines are unchanged.

Exact live manifest validation and CPU bootstrap passed; the cloud browser cannot create WebGL2 and cannot reproduce the later native-browser failure. This candidate is **diagnostic-only, not yet published or native-browser accepted**. See `docs/startup-diagnostic-receipt.json`.

## Provenance and status

This is a **new reconstruction**, not a recovered copy of either lost unpublished candidate. Stable engine/renderer/assets originate from exact Sites19 V11.1 commit `0a5f07447719117a0084cffb9a525a1cd1e54ea3`; hardened authority originates from verified public-alpha commit `55067c6dc71f299bf9e35fee80b54dfc2d7ee8e1`. New source hashes and receipts are recorded separately. No frozen history is rewritten.

**Protocol 3 candidate, not yet remotely accepted:** the live reconnect patch `6269e2b77b2f3c840d13afe3bd7ca3e91828785c` measured a 484.364 ms event-loop gap with only 1.631 ms process CPU in that sample; the old guard honestly ended the race. This candidate makes a visible, bounded server interruption an explicit race rule instead of silently catching up or immediately failing every isolated stall. Only `https://kerala-roadster-multiplayer-alpha.onrender.com` is approved. See `docs/interruption-patch-receipt.json`; old protocol-2 receipts remain historical evidence, not acceptance of this protocol.

## Online rules

One public room, two real connected seats, equal stock red-model physics, non-contact. No traffic, flight, ultra boost, accounts, coins, upgrades or payouts. Both drivers load matching assets and ready; the host starts. Server owns clock, checkpoints, recovery penalties and results. Client sends only validated bounded controls and interpolates authoritative poses; no prediction, local finishing or result submission.

There is **no player pause**. Lobby, blur and background neutralize controls; an otherwise healthy server race continues. A server backlog over 250 ms freezes both cars, checkpoint/recovery state and the simulation race clock. Backlog is discarded, not fast-forwarded. The server clears inputs and sends one shared interruption generation, then waits for 500 ms without another threshold-crossing gap before resuming with another generation. Old and during-hold controls cannot apply afterward; drivers must press controls again. No client can request or prolong this hold.

Limits are at most 2 seconds per interruption, 3 interruptions per race and 5 seconds interrupted in aggregate. The lost gap and stable hold both count. Exceeding any limit ends unfinished drivers as `DNF / server-interrupted`; already completed results remain valid. The banner and results disclose server-confirmed interrupted time separately from race time. Rematch resets the budget. This can recover bounded scheduler jitter, not make an overloaded free host real-time; repeated or sustained stalls still fail honestly.

Stale inputs brake; stale snapshots freeze and stop inputs. Reconnect remains bounded to 20 seconds of **wall time**, including interruptions, with rotated private tokens. Expired disconnected seats receive DNF, never a fabricated finish. Server restart loses temporary rooms; free hosting may sleep or restart.

The entry reads/writes **no solo garage or currency save** and invokes no seven-car migration. Optional reload recovery uses only its own endpoint/build-scoped sessionStorage key. No old solo entry is bundled. Automated test driving modules are test-only and never offered as online AI opponents.

## Local commands

Tested Node24.19.0:

```sh
npm ci --ignore-scripts
npm run build
npm test
npm run test:authority
npm run test:physics
node tools/verify_water_raycast.mjs .
PORT=8787 npm start
```

Open http://127.0.0.1:8787 in independent browser profiles. Node tests are not real browser/GPU/human acceptance.

## Deployment gates

Prebuilt exact package, one Node service. Build `npm ci --omit=dev --ignore-scripts`, start `npm start`. Public bind requires explicit PUBLIC_ALPHA=true plus Render-provided RENDER=true, RENDER_EXTERNAL_HOSTNAME and PORT. No arbitrary origin configuration or credentials are introduced.

Use only the owner-approved free plan/region, autoDeploy:no. First publish/deploy disabled package. Verify exact initial commit, service origin, free plan and region before preparing an origin-pinned activation build. Hold activation branch changes until the initial deployment revision is confirmed (prefer terminal/live), then publish and manually deploy the exact activation revision. Verify remote HTTP/WSS and independent clients before claiming playable public multiplayer. This code creates no services, accounts or paid resources.

Static content is a startup size/hash/URL allowlist with bounded streaming, exact CSP,16 concurrent streams maximum,64MiB burst/128KiB per second shared byte budget,304 revalidation and no backend/source fallback. Existing alpha Host/Origin, room, connection, message, control-frame, heartbeat, payload and backpressure guards remain. Origin checks are not authentication. This is a small experimental alpha, not production anti-cheat or durable persistence.

## Acceptance and rights

See docs/acceptance.md and docs/activation-receipt.json (the original reconstruction receipt is retained separately). Stable V11.1 reverse/steering/recovery is preserved; world/collider bytes match client and authority. Actual GLB CPU scene/water tests do not imply GPU rendering. Browser, GPU, physical human driving and **protocol-3 public-internet acceptance** remain pending. A historical protocol-2 no-disconnect full race passed; that does not validate this new timing rule or live reconnect.

LICENSES.md corrects unauthorized assistant CC0 descriptions for original work without granting a licence or rewriting history. Genuine MIT and ODbL notices/provenance are preserved. Public package excludes private references, IDs, notes, credentials and old solo entry. A tested source archive is saved to Library before publication handoff.
