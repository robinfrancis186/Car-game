# V17 R3.4 — one reference-derived UI, plus local leaderboard

Unpublished UI-consolidation candidate. R3.3 is preserved separately as a frozen checkpoint. This candidate includes R3.3's local leaderboard and HUD containment fix; no deploy or push is part of this work.

## Evidence and design decision

The four authoritative reference files were downloaded and visually inspected. Their actual contents—not earlier swapped labels—are recorded in `tests/v17/r3-4-evidence/REFERENCE_MANIFEST.json`: Home is `PRIVATE_LIBRARY_REFERENCE`; Results is `PRIVATE_LIBRARY_REFERENCE`; Workshop is `PRIVATE_LIBRARY_REFERENCE`; Shop is `PRIVATE_LIBRARY_REFERENCE`. None of those reference images is copied into the runtime.

The user's latest instruction to avoid duplicate Play/actions takes priority over the Home reference's duplicated bottom Play item. The retained language is an orange gradient primary action, dark translucent outlined secondary controls, consistent icons/type and 8px control corners. Mobile changes layout, not the button theme. This is reference-derived implementation, **not a claimed pixel-exact match**.

## Runtime changes

- One Home **PLAY** opens setup. Bottom navigation is **EVENTS**, not a second Play/launch. Setup keeps the explicit **START RACE** or **EXPLORE KERALA** action.
- Home and global **GARAGE** consistently open Owned cars. **WORKSHOP** and the inspection tab explicitly open tuning. Removed the redundant Garage shortcut from setup.
- Removed hamburger and gear aliases that opened the same Help panel. One **Help & settings** utility remains, alongside Sound.
- Home leaderboard is a matching trophy utility rather than a fourth action-grid row. The approved three-row Home layout and car space are preserved on mobile. Results retain explicit name entry and the leaderboard link.
- Global Enter now follows the same hierarchy: Home opens Events; a separate fresh Enter from Events starts. Key repeats cannot skip setup, and focused controls/modal inputs retain their own behavior. This fixes a reproduced keyboard inconsistency, not a proven explanation for the earlier unexpected Mac race observation.
- Shared primary/secondary/utility/selected/disabled/focus tokens replace differing Home, Start, Story, Pause, Results and leaderboard button palettes. Existing accessibility and touch-sized controls are retained.
- **Confirmed dock occlusion fixed:** at 1222×619, the dock began at y542.525 while collection and Workshop scroll areas extended below it. Both content bottoms now derive from the same responsive dock height and bottom inset plus 12px clearance. Upgrades and card actions remain scrollable and visible; they are not hidden or brought above the dock with z-index tricks.

## Preserved behavior

R3.3's explicit-save, device-local leaderboard remains: safe names, IME composition handling, per-track/mode/route/Story rankings, millisecond ties, run deduplication, protected storage and nonfatal session-only fallback. See `R3_3_CHANGELOG.md` for details.

Original assets, physics, courses, seven cars, wallet/profile/Story storage and the R3.2 graphics-interruption safety behavior are unchanged. No existing user save is reset. No leaderboard names are sent to a server.

## Validation scope

Final command results, source/build hashes and preserved-file counts are recorded in `tests/v17/r3-4-evidence/FINAL_RELEASE.json` once generated. New checks include actual-controller navigation/Enter behavior under fine/coarse input fixtures, one Play/one Help ownership, leaderboard focus return, shared style-role declarations and dock geometry anchored to the real Mac measurement.

The supporting static previews now use current source hashes, no stale removed-control bindings, and explicit game-only leaderboard controls. Their old folder names/manifests are historical provenance. Static preview smoke and synthetic negative fixtures do not substitute for the real game.

**Still required:** native desktop and mobile rendered comparison, scroll-to-last-upgrade/card-action hit testing, actual race → name → Save → reload, GPU context-loss recovery, performance and audio. The apparent blank Garage/Shop thumbnails remain undiagnosed despite decoded visible PNGs; no speculative thumbnail change is included. No deployment has occurred from this candidate.
