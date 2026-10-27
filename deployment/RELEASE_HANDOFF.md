# V17 R3.13 local candidate — not published

Includes frozen mobile 72b8d8b and pursuit 1ed00b7 through integration eff8ea2. Frozen originals remain unchanged.

Concrete fixes: finished rivals clear the Hot Pursuit safehouse; Auto brakes against relative traffic speed and future road support height, while real barriers remain blocking; racing Auto uses the existing police curve envelope. Early traffic warnings, explicit Boost release/recharge and queued short Ultra taps improve input clarity. Close-patrol recovery is blocked; recovery cannot manufacture an escape through teleport separation, and a safehouse finish requires returning to its real location.

Balance is explicit: Hot Pursuit has one advertised regroup between 32–52 race seconds, target cap 18m/s through ordinary acceleration/deceleration. Original 43m/s outside that window. Capture, collisions, 130m/110m separation hysteresis and eight-second escape remain active. This is an authored opportunity, not passive immunity. Exact original hashes and 54other unchanged gameplay methods remain guarded; changed method tests replace only the reviewed exact scope.

Validation: 69aggregate stages; native real-time touch escapes in 844×390 and 390×844 without Ultra, damage or recoveries; actual retry/name entry/save/duplicate-submit/reload plus held-brake capture; 40touch-layout cases, native simultaneous controls and orientation release; three Manual/Auto switching cases. Native Mac viewport tests do not replace phone, Safari, listening or new-player acceptance. Prior interrupted and harness-failed runs remain in local evidence. The benchmark completed all ten raw sample blocks before a summary-only variable error; corrected aggregation uses those unchanged samples without omitting any block. The obsolete 26m/s opening and earlier failed strategies are rejected evidence, not final results.

Build: npm --prefix web run build; node tools/build-static.mjs -> dist/vercel. Runtime manifest enumerates 188 exact public files including all existing licences. No public assets, collision geometry, approved Home, map definitions, wallet, save or multiplayer validation modules changed. Legacy unchanged CC0 audit exception disclosed. See performance-summary for bounded paired results and cadence limits; no 60 FPS or 9/10 claim.

No source push, Library source upload or deployment authorized in this turn. Parent owns publication after explicit approval. Last parent-confirmed live R3.11 remains the rollback reference; frozen R3.12 has not been represented as live.
