# V17 R3.8 local release candidate

Parent owns Git publication, Vercel publication and live verification. This branch has not been pushed or deployed. Preserve live R3.7 at a642f06df4603c2eff6f0f499f92bf3def5bea3f for rollback. R3.7 metadata is retained in deployment/history/r3-7/.

Build the exact split runtime with `node tools/build-static.mjs`; publish only `dist/vercel`. `deployment/runtime-manifest.json` maps every public byte to committed source and SHA-256. Its content tree excludes release.json to avoid self-reference; the full tree includes it. The standalone is rebuilt with `npm --prefix web run build`, then verified with `python3 tools/verify-standalone.py` (its legacy report directory tests/v17/r3-2-evidence must exist). Dependencies are pinned in web/package-lock.json.

60/60 aggregate checks, all 11 destination launches on two viewports, stale selections, save/history, Auto/manual keyboard/touch lifecycle, Story/capture and protected-file checks passed. No preservation hash or surface test assertion was weakened. See publication-checks.json and r3-8/validation/. The legacy payload audit still rejects unchanged CC0 character grant metadata; no grant was stripped to satisfy it.

Auto controls pedals only and resets off for each new run. Normal modes and Story use it; the experimental wall test remains manual. Boost and steering remain player input. This repository currently has local leaderboard validation and no multiplayer server.

The small NVIDIA pilot uses CC BY 4.0 assets, not the full dataset. Genuine USD source dependencies, licences and reproducible Blender conversion are under assets/simready/. Public attribution is in LICENSES.md and Help; the full licence ships in public/licenses/NVIDIA_CC_BY_4.txt. Pilot props are visual-only, with no new collision proxies; measured foot clearance is approximately 4cm under the existing asset convention.

Mac Chrome frame timing is bounded emulation. Visible-pilot mobile-sized rendering includes two extra instanced draws and 26,838 triangles. No physical-phone, Safari or listening tests were run. Current buildings, foliage, vehicles and characters remain stylized; this is not full photorealism.
