# V16 original surface-contact proof

This is a separate working copy of frozen V15. The reference review inspected 381 unique frames, including dense samples of wall, tube, loop and landing transitions; it did not inspect all 3,628 frames. Source-derived images/video remain analysis-only outside the project.

## Achievable first slice

An optional **solo surface test**, not a normal race: level approach, smooth bank to a 90-degree wall, supported wall hold, smooth return to level, broad runout. The canonical `surface_profile.json` defines a 900 m original ribbon, 12 m wide, with its center 8 m above ground. Both Blender and model consume that profile. The surface position is `[s, 8 + lateral*sin(bank), lateral*cos(bank)]`; longitudinal derivatives include the lateral bank-change term, so collision and orientation use the real local surface normal rather than an unrelated car roll animation.

- Independent fixed-120-Hz contact model: tangent momentum, steering, braking, grip, projected gravity and a documented finite arcade adhesion limit.
- Meaningful edge/low-speed/adhesion release into world-gravity flight, finite recontact or safe return. Reverse, pause, restart and recovery are explicit contracts.
- Render the actual contact frame and blend a local-up chase camera continuously. Existing ordinary cameras are untouched unless the optional model supplies its surface frame.
- Solo only: no AI, pursuit, coins, lap reward, boost refill, thruster flight or flip. No attempt to disguise bots as multiplayer. Existing V15 races retain their ramp/airtime and aircraft mechanics.
- Existing car ownership, tunes, balance, storage namespaces and story remain unchanged. Use an already-owned car; no automatic purchases or save resets.

## Acceptance

1. Analytic orthonormal frames, derivative agreement and exported mesh/contact ray checks across 0/30/60/90 degrees and transition seams.
2. Deterministic physics at 30/60/120-Hz outer updates, all seven cars, stock and tuned, steering/brake/reverse, stationary/edge/airborne/reset/pause cases.
3. Actual car wheel/pose/contact and camera frustum/continuity tests, with no car-only decorative roll.
4. Normal V15 physics/economy/save/asset hashes and existing regressions preserved.
5. Native GPU/driving acceptance remains required after a tested, durably backed-up candidate. Target no material regression from normal route cost; proposed added road-art budget below 30,000 triangles and about 12 material draws, not an observed FPS claim.

## Explicit limits

No ceiling traversal, closed tube, full loop, arbitrary rigid-body vehicle dynamics or manufacturer-realistic adhesion is implemented by this slice. Camera local clearance is not universal scene collision avoidance. The video does not establish an exact boost formula. No private reference media or new reuse-license grant belongs in the public payload.

## Ownership

Model worker: new surface-ribbon/surface-drive/stunt-model modules and numerical tests. Asset worker: canonical-profile Blender route geometry and new course metadata. Lead: optional route/UI admission, local-frame renderer/camera, tests and backup. Existing V15 files are immutable. Any demonstrated V15 native defect takes priority over this new work.
