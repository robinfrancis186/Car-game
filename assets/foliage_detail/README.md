# V10 bounded foliage detail

Original procedural geometry and vertex colors. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. No photos, downloaded geometry, alpha-cutout textures or new collisions. This is stylized geometry, not a photogrammetric tree/tea scan.

## Runtime contracts
- `HighlandShadeTreeNear.glb`: 5,688 triangles, two materials/draws. Replace the full old HighlandShadeTree at the exact existing transform. Its 168 original bark/trunk/structural-branch triangles are preserved exactly. All new leaves/twigs are visual only. Materials: `Highlands_Tree_Bark`, `Highlands_Shade_Leaf_Detail`.
- `TeaLeafCluster.glb`: 160 triangles, two materials/draws. Ground-rooted irregular shrub, four small dark interior foliage lobes, 36 individual pointed outer leaves and four basal stems. Bounds X±0.62 m, Y0..1.219 m, Z±0.61 m. Materials: `Highlands_Tea_Stem_Detail`, `Highlands_Tea_Leaf_Detail`. Leaf motion must use a 0..1.22 m height mask, not the tall-tree mask.
- Native library `Highland_Foliage_Detail.blend` has named appendable collections for both assets. Blender Z up; glTF Y up, +X forward.
- `tea_detail_rows.json` contains 212 clipped runs of the unchanged authored tea rows: 7,318 points/7,106 segments, clipped within 110 m of the race route. Points are THREE [x, groundY, z], not canopy-top positions; cumulative distances preserve original row phase.
- `tea_placements_reference.js` has no imports and exports `sampleTeaTerrain`, `buildTeaPlacementIndex`, and `selectTeaDetailPlacements`. Use the reference function, not a second independently randomized scatter.
- Placement IDs and transforms are deterministic. Two staggered bands at ±0.52 m, 0.70 m pitch, 0.35 m stagger; small stable yaw/lateral/scale variations. Final root Y uses the exact triangle terrain sampler after offsetting X/Z.
- High: radius 85 m, max 1,250 shrubs =200,000 triangles. Balanced: radius 50 m, max 500 =80,000 triangles. Selection has a spatial-grid index and returns a conservative `coverage_radius_m`; fade old coarse tea only inside that complete coverage, around the LAST SELECTION CENTER. Outside coverage or budget, retain the old row. Near/far dither is renderer-owned.
- The coverage radius also shrinks near the authored clipping boundary. Off-road flight must not fade coarse rows where no near replacements were authored.

## Evidence
- `binary_validation.json`: actual buffer triangles, bounds, finite vertices/normals, zero degenerates, vertex-color presence, no images/external buffers; exact old bark triangle preservation; unchanged mesh/grid/collider hashes. Builder-owned Explore metadata changes are distinguished from unchanged physics fields.
- `tea_placement_fixture.json`: exact first 20 placements for the declared query; pure JS reference reproduces every value.
- `placement_validation.json`: exact fixture and terrain roots, bounded budgets, off-road coverage guard.
- `renders/foliage_detail/Tree_Before.png` and `Tree_After.png` are actual course-side camera views, not studio renders.
- `Shoulder_Before.png` / `Shoulder_After.png` show actual tea replacement from the road shoulder. `Driver_After.png` gives the forward road context. These are CPU Blender previews, not browser/GPU or frame-rate evidence.
- Generators: `blender/build_foliage_detail.py`, `plan_tea_detail.py`, `render_foliage_detail.py`; actual asset QA `blender/validate_foliage_detail.py`.

## Far canal performance asset
The later authorized optimization adds `CanalRainTreeFar.glb` only; the original canal tree remains byte-identical. It retains all 2,836 original bark triangles and exact total bounds. Its distant-only crown has 33 rounded envelopes derived from the 38 original crown clusters, 660 triangles, for 3,496 total / 2 draws. Use the original detailed tree close to the camera with a matched transition; the low-detail envelope is not intended for close inspection. No collider or coast placement change. Native source `CanalRainTreeFar.blend`; generator `blender/build_canal_far_lod.py`; actual-buffer evidence in `aux_art_validation.json`.
