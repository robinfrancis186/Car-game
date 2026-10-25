# V17 UI-consolidation static review (not the game)

The folder name is historical. The generator now reads current source bytes and
records their exact hashes in source-anchors.json. Earlier R3/R3.1 manifests are
provenance only, not the identity or acceptance of this candidate.

This review uses real current HTML/CSS and original-model PNG thumbnails with
synthetic state. It has no WebGL, race simulation or real save access. Leaderboard
controls are explicitly disabled as game-only; use the actual standalone for
leaderboard input, persistence and native gameplay acceptance.

Build: node build-review.mjs
Smoke: node review-smoke.test.mjs
Hit-target/dock negative fixtures: node ../../web/tests/v17-r3-1-hit-targets.test.mjs

The browser audit can check actual CSS hit targets, header and dock occlusion,
including scrolled Workshop upgrades and collection card footers. Synthetic
fixture passes do not prove rendered/native acceptance. No exact-reference
pixel-match, 3D scene, FPS or audio claim is made.

Authoritative current checks: ../../tests/v17/r3-4-evidence/FINAL_RELEASE.json
