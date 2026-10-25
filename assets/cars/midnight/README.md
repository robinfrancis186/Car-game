# Midnight Meridian GT — reconstructed original car

This is a newly reconstructed, fictional dark-blue luxury hypercar, not recovered V12 bytes or manufacturer CAD. A user-supplied visual reference informed the arched central intake, rounded haunches, side channel and cyan lower accents. There are no logos, photographs, downloaded model parts or embedded textures.

## Native and runtime assets
- Editable native: `Midnight_Meridian_GT.blend`, 317 individually named Blender meshes.
- Generator: `blender/build_midnight.py`; shared, read-only original project primitive/wheel serializer: `blender/rebuild_car_helpers.py`.
- Runtime `car_midnight.glb`: 75,670 triangles, 30 material draws, nine PBR materials. `manifest.json` records the exact hash and dimensions.
- Units metres. Native +X forward/+Z up; glTF +X forward/+Y up/−Z left.
- Hierarchy: `CAR_ROOT > CarBody`; separate Hood, two DoorHinge/door assemblies, fixed RearWing. Each wheel has independent Steer/Spin/Wheel nodes; Caliper is a nonspinning child of Steer.
- Nominal wheel radius .366 m; actual exported outer groove radius .366103 m, hub height .368 m, minimum tire Y .001897 m. Wheelbase2.7 m, hub lateral ±.924 m.
- Max tested visual steer±.45 rad. Cosmetic body roll±.008, pitch±.005, heave±.002 m. Hood opens .60 rad about glTF+Z; Left door −Y/Right door+Y, .70 rad. RearWing is fixed—no active-wing hinge/API.
- Paint slot intentionally retains common runtime name `Crimson multi-coat | original fan concept`; its authored base color is midnight blue, not red.
- Fictional boost mounts: `[-2.4,.255,±.56]`; these are game VFX sockets, not a production flight claim.

## Verified scope
Actual GLTFLoader validation covers finite/unit normals, zero-area faces, hierarchy, wheel radius, independent spin/fixed calipers, bounds and budgets. Blender reimport tests cover756 combined body/tire pose samples,364 alloy/rotor-to-caliper rotation samples, fixed wing, and discrete open-door/hood positions. Closed panel seams may intentionally touch; all tested open positions are clear.

Minimum **sampled** tire-vertex/body distance at nominal body pose and zero/full steering is33.62 mm; separate sampled caliper-vertex/alloy distance is6.47 mm. These are discrete mesh tests, not continuous mechanical clearance or real vehicle engineering certification. Runtime gameplay/browser rendering is validated separately by the integrating developer.

Blender's hardened Boolean bevel produces some invalid corner normals. The export-only `clean_export.py` preserves all positions and valid manufactured normals, removes one float32-degenerate triangle, and fills63 invalid corner normals from their surviving incident triangle geometry. It does not repaint the model or move vertices. This preserves smooth fender highlights rather than accepting a visibly striped no-hardening workaround.

Front/rear/thumbnail images are renders of the **actual exported GLB**, not a different beauty model. CPU Cycles, no denoising backend available. Transparent512×320 PNG thumbnails are compressed losslessly when needed; no reference pixels or AI painting.

Original project geometry; reuse license not selected by owner. Existing third-party software notices remain unaffected.
