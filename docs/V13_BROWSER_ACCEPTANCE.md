# V13 exact-version browser acceptance

Run only after the frozen candidate is deployed and its HTTP hashes match `tests/release/V13_RELEASE.json`. Do not reset, top up or spend an existing user's coins to test purchases. Browser tests of paid tiers may use a genuinely separate, explicitly authorized QA profile; otherwise source tests cover that part and the human purchase check remains pending.

1. Record the existing car, coin balance and installed levels before loading. Confirm V13 preserves these after migration and reload; base cars remain free. Do not infer the player's current balance from an older screenshot.
2. Home has one PLAY entry, GARAGE and MAP. PLAY opens mode choice. Help → Credits exposes legible linked OSM/ODbL and other required notices. Check 320×568, 390×844 and landscape/desktop; essential actions must remain accessible.
3. Inspect Silver in the real 360-degree garage and on road: neutral glazing, refined contours, spinning/steering wheels, no body/tire interference. Compare the same car/pose/quality with the earlier version where feasible, not different screenshots presented as an A/B measurement.
4. Inspect actual installed upgrade finishes. Base/level1 brakes are red; level2 orange; level3 violet. They must not recolor another car, alter orange/violet arcade flame meaning, or override chosen body paint. Purchase/performance tests require a permitted QA profile; level0 must retain prior braking behavior.
5. Start Story chapter1. Intro is four seconds, model/countdown/input/audio remain frozen, Skip/Enter/Space work. Escape/hidden/blur goes to the briefing without auto-resume. Reduced motion bypasses shots. Test quick races still operate independently.
6. Complete the chapter legitimately: the normal reward and story completion settle once, then a three-second success shot may play only in the safe near-end road corridor. Unsafe/delayed/failed outcomes show results immediately. Reload must retain chapter unlock without granting another reward.
7. Observe asphalt normal/roughness scale, shoreline reflection environment, contact shadows, fuller showroom plants and floor. Inspect for shader errors, texture shimmer, missing surfaces and transparent-glass issues. Sample identical High/Lite poses with diagnostics; source tests are not a GPU budget guarantee.
8. Pause/resume/mute, flight/boost, recovery and reverse contact escape remain functional. Record audible evidence only if actually listened to. Diagnostics audio targets alone do not establish sound quality.

This is a short original story slice and an incremental stylized visual improvement, not a full campaign, cinematic replay system or manufacturer simulator. No multiplayer is newly enabled here.
