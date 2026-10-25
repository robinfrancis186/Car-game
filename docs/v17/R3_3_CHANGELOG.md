# V17 R3.3 — device-local leaderboard and HUD width fix

Unpublished candidate based on the exact R3.2 source. No deploy or push is part of this patch.

## Changes

- **HUD containment:** a measured Mac Chrome defect at 1222×619 CSS pixels had a 170px speed cluster containing 232px vehicle bars. The bars and boost label ended at x1261, 39px outside the viewport. `max-width:100%` now clamps the bars to the responsive parent; it does not hide or clip the controls. The source cascade regression reproduces the original geometry and checks 32 viewport/pointer cases. Native rendered verification of this candidate remains required.
- **Leaderboard — On this device:** Home and race results open an accessible, scrollable leaderboard with Back/Escape and focus restoration. Successful eligible races offer an optional name field and explicit **Save time** action. Enter in that field saves rather than restarting the race. Typing/opening the board never saves a name.
- Records compare only the same track, mode, actual route endpoints and Story chapter. Times display milliseconds; exact ties share competition rank. A run ID can be saved only once, even after repeated clicks or reload. Explore, experimental surface tests, failed/aborted runs and graphics-interrupted sessions do not qualify; Story must satisfy its completion objective.
- Names are trimmed, Unicode-normalized plain text, limited to 24 code points, with control/invisible-format characters rejected. Names are rendered with `textContent`, never HTML. Confirming an IME composition (for example while entering Malayalam) does not prematurely save; a subsequent ordinary Enter saves the completed name.
- The isolated `malabar-leaderboard-v1` storage key holds at most 200 records. There is no account, backend or network transfer. Invalid/future saved data and detected cross-tab changes are protected rather than overwritten. Storage access/quota errors leave gameplay usable and clearly mark new records as session-only. At capacity the game refuses a new record rather than silently deleting old records.

## Preservation

No changes to original game assets, courses, car catalog, physics, wallet, profile or Story storage modules. The existing R3.2 graphics-loss freeze/reload behavior is preserved. Existing saved coins, owned cars and Story progress are not reset. The leaderboard is browser/origin-local, not global or shared between the review and production sites. Clearing browser data removes local records.

## Validation and limits

Authoritative final results and hashes are in `tests/v17/r3-3-evidence/FINAL_RELEASE.json` once generated. New checks cover the measured HUD cascade, valid/invalid names, millisecond ties, partitions, deduplication, malformed/future storage, quota/access failures, concurrent changes, actual-controller integration and a race finished through real simulation with a stub renderer.

Node simulations and source/CSS math are not a rendered browser or GPU pass. Native R3.3 HUD bounds, keyboard/touch layout, race-to-save-to-reload and 3D regression checks remain acceptance gates. The pre-existing static UI preview exercises its historical views; it does not implement the new leaderboard interactions. Use the real split app or standalone for leaderboard acceptance.

The apparent blank Garage/Shop thumbnails remain **unresolved, not a diagnosed load failure**: Mac evidence showed decoded 512×320 PNGs with visible nonzero layout, and source/embedded PNG bytes match. No speculative thumbnail edit is included. The separately reported unexpected race transition also has no established cause and is not claimed fixed.
