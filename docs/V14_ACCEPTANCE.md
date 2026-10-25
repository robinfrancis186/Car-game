# V14 interface acceptance checklist

This release changes presentation/accessibility only. It keeps the exact V13 profile/story namespaces and all protected simulation, economy, renderer, audio and asset bytes. No asset/model redesign or multiplayer activation is included.

## Required evidence
- [x] Fresh V13 baseline screenshots inspected before edits; user Pause image inspected.
- [x] Independent 24-surface / 87-control inventory and protected-source identities.
- [x] Parent-provided native V13 findings recorded with explicit provenance/uncaptured states.
- [x] Coherent V14 after-captures at 1180×757, 390×844, 320×568 and 568×320; each capture checked for actual intended visible state.
- [x] Every top-level screen, ordinary modal, HUD, Story overlay, collection state and Help/settings/Credits reviewed. Loading/error/failure/empty/max/protected-save states clearly marked synthetic where not naturally reached.
- [x] Help header/Close visible at top, middle and bottom scroll in the CSS preview; source focus/Tab/Escape and nested Help→Pause contracts pass. Actual main native focus remains follow-up.
- [x] First/last event car, Owned/Shop card and upgrade action reachable; clipped regions have visible scroll affordance; compact car choices don't permanently cover preview.
- [x] Consistent Play/Garage/Map/Shop naming, contextual owned/locked inspection, practical factual Pause/result copy.
- [x] Focus/disabled/selected state readability, target size, safe-area layout, no critical HUD/control overlaps. No claim of full accessibility conformance from screenshots alone.
- [x] Enter/Space on native disclosure, select, links and buttons must not start a race or toggle pause unexpectedly.
- [x] Loading prevents covered background activation; failure offers an accessible real reload action; success restores ordinary interaction.
- [x] Protected modules/assets pass hash check; independent main.js diff and controller tests show no new spending, resets, reward duplication or simulation changes.
- [x] Full npm test, standalone build and split/embedded byte identity pass.
- [ ] Complete source/checkpoint uploaded durably, exact release and hosting hashes recorded.

## Native follow-up (separate from CSS approval)
Verify the same screens against the real 3D hero/world, not just neutral preview backgrounds. Preserve the existing profile; don't spend/reset coins for testing. Test keyboard and touch-like controls, actual HUD readability on road, pause/help focus and dismissal, menu transitions, Story skip/result settlement and native viewport restoration. Point FPS samples are not a benchmark; actual listening is required for any audio-quality claim.

## Evidence identity
R2 independent source review: `tests/ui_audit_v14/independent_final/REVIEW.md` and reproducible archive (SHA256 2952247d6ba1f707fafe157308d2c88681108977bd9ba96bb58133263bca0438). R1 direct pixel review: `LEAD_R1_RENDER_REVIEW.md`; final R2 rendered recheck passed in `r2/ACCEPTANCE.md` and `LEAD_R2_RENDER_REVIEW.md`. Source checks do not substitute for native focus or graphics acceptance.
