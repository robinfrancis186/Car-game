# V17 R3.12 — phone driving usability candidate

Parent owns publication. No remote push or deployment from this worktree.

Base/rollback: b5ee467193537370a4690fb040a048f5da6b61fa (live R3.11).
Build: `node tools/build-static.mjs` -> `dist/vercel`; exact public-path/source-path/size/SHA mapping is `deployment/runtime-manifest.json` (187 files).
Standalone: `npm --prefix web run build`; integrity receipt is in validation.

Only touch gameplay layout and controller pointer bookkeeping change. Primary steering, Go, Brake, Boost and Ultra remain direct; Reverse/Reset/Flight/Flip are in More. Touch Boost also accelerates; keyboard Shift preserves independent throttle. Rotation releases captures and pauses, requiring Resume; browser bar resizes with unchanged orientation do not pause. Portrait remains playable and tip can be dismissed. No sensor or security setting changes.

67/67 aggregate stages passed with the final controller. Landscape CSS aligned Boost/Ultra with the right edge, and closing More explicitly releases hidden held pedals. Six affected UI/layout/controller checks plus native touch/safe-area, tray-close regression and paired landscape performance passed. Exact main/test preimage hashes and CSS scope record identify these post-aggregate changes. 40 layout cases cover five sizes, Manual/Auto, tray closed/open, and ordinary/large simulated side insets. Actual Chrome touch dispatch validates simultaneous steering/boost/brake and rotation/cancel at all five sizes. Eight accelerated genuine-model browser cases cover complete Coast/Highland time trials, once-only award/name/save/reload, natural police capture and timer failure/retry in both orientations. Model state/position was not injected for completion. Home and matched desktop gameplay pixels are identical. Native paired performance is bounded Mac evidence only.

The initial progression harness used a 25-character name and expected it unchanged despite the 24-character input limit; corrected names passed with original product validation unchanged. One existing synthetic two-finger fixture had reused pointer ID 1; it now uses IDs 1/2 without removing assertions.

No new assets, meshes, collisions, downloads or licences. Existing capture-driver CC0 metadata audit exception is inherited and disclosed. Physical phone/Safari/listening/new-player acceptance remains outstanding. Do not call this a finished 9/10 game. Separate pursuit candidate 1ed00b7 is excluded and requires its own remaining review.
