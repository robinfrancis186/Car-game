# Optimized Kerala environment / course GLBs

Generated from the original Blender library and latest OSM-derived native course by `blender/export_web_assets.py`; originals are untouched. These browser exports are also copied into `web/public/assets/`.

## Browser integration

Load with Three.js `GLTFLoader`. No Draco/Meshopt decoder or external image texture is required. Each prop is merged into one mesh per material; palm leaves retain their original hue variations in the glTF `COLOR_0` vertex attribute. Preserve vertex colors and two-sided foliage materials.

Geometry is already **Three.js Y-up**. X is east/vehicle-forward at zero yaw, -Z is north. glTF root/mesh transforms are identity; do not apply an extra -90-degree rotation. Original Blender [x,y,z] positions become Three [x,z,-y]. A Blender yaw around +Z becomes the same positive yaw around Three +Y.

`course_runtime.json` has:
- `route_points`: smoothed Three XYZ route, including road elevation Y=0.18 m.
- `checkpoints`: Three XYZ.
- `prop_instances`: `asset`, `position`, `yaw_rad`, uniform `scale`.
- `course_meshes`: file names and original collision-intent flags; flags do not implement physics.
- OSM attribution and provenance notes.

For instanced rendering, batch each prop's material mesh in an `InstancedMesh`, preserving its source geometry/material and any world transform. Use distance/frustum culling rather than rendering all 1,538 placements at full detail. Optional palm `*_LOD1.glb` files lower each palm from 4,142 triangles to 1,094. Tune LOD distances against actual browser performance; no universal frame rate is promised.

Palm vertices are locally Y-up: leaf crown spans roughly Y=6.7–9.9 m. A gentle x/z displacement can animate leaves without moving the trunk; apply consistent displacement to shadow materials if dynamic shadows are used. This is an aesthetic wind effect, not a physical tree simulation.

## Approximate budgets

| Asset | Triangles | Material draws | KiB |
|---|---:|---:|---:|
| Each palm | 4,142 | 4 | 219 |
| Each palm LOD1 | 1,094 | 3 | 79 |
| House | 6,041 | 11 | 374 |
| Fishing boat | 2,634 | 4 | 80 |
| Road reflector | 136 | 3 | 13 |
| Grass clump | 480 | 1 | 15 |
| Course road | 17,156 | 3 | 529 |
| Course terrain | 1,491 | 2 | 46 |
| Course water | 1,353 | 2 | 99 |
| Course furniture | 5,588 | 4 | 430 |

All 16 environment/course GLBs total approximately 2.30 MB. Exact current counts, sizes and SHA-256 hashes are in `environment_web_manifest.json`.

## Validation performed

All 16 exported GLBs were re-imported into Blender. Checks passed for finite geometry, zero degenerate polygons, dimensions, file hashes, upward course surface normals, and palm vertex-color/two-sided material attributes. Actual optimized palm, house and boat render previews were inspected. The simplified roof and foliage are lower-detail on purpose, not replacements for the original high-detail Blender source.

`environment_web_validation.json` and logs contain the results. Blender CPU previews are not browser gameplay screenshots. Browser gameplay/performance tests belong to the main web application test record.

## Terrain hole repair / dry-land detail (2026-10-22)

An actual Mac gameplay screenshot exposed the sky through a missing ground region near route distance 2,200 m. This was a polygon-with-holes triangulation failure, not simply a brown ground material. The terrain now uses Blender constrained Delaunay triangulation with every shoreline/lake edge constrained before dry-land triangle classification. Water surfaces, exact route/checkpoints, and all other mesh binaries are unchanged.

- Corridor audit: **919/919** expected-dry samples covered, up from 733/919; all 10 lateral samples at s=2,200 m now hit terrain.
- Lake-edge audit: **2,350/2,350** dry-side ray hits, **0/2,358** TropicalGround intrusions on the lake side. Samples are 0.2 m and 1 m normal offsets from every lake segment midpoint, avoiding sub-millimeter float32 ambiguity from nearly tangential offsets.
- Ocean shoreline audit: **122/122** dry-side ground hits and **122/122** sea-side water hits.
- Added **516 original TropicalGrass clumps and 83 secondary palms**, concentrated on s=2,200–4,350 m. Every added conservative root footprint is on dry land and outside the road. Minimum centerline distances are 5.899 m for grass and 17.040 m for palms; full footprint clearance is checked separately.
- Original **939** prop transforms remain an identical prefix; total placements are now **1,538**. Grass is visual-only. Added palms use the application's normal palm-collider creation, so gameplay obstacle regression tests must use the refreshed runtime JSON.
- Source/export hashes, full counts, before/after coverage and all checks are persisted in `terrain_repair_qa.json`; detailed reproducible tests are in `assets/course/audit_terrain_coverage.py` and `assets/course/validate_terrain_repair.py`.

The lake-hole test targets TropicalGround. The unchanged continuous beach ribbon can pass beneath the lake mouth; an independent GLTFLoader grid found four GoldenSand hits 3 cm below the opaque lake surface, not exposed dry land. It also confirmed all 1,491 terrain normals face up and found zero dry misses in 2,167 additional full-route samples.

Independent Three.js GLTFLoader/Raycaster evidence is preserved unchanged in `kerala_independent_glb_qa.json` with reproduction script `kerala-terrain-ray-audit.mjs`. `terrain_repair_diagnostic.png` is a technical top-down projection of actual before/after GLBs, explicitly not a browser screenshot.

No new texture or external model was introduced; the existing original Blender grass/palm GLBs are instanced. Browser screenshot and performance validation are recorded by the main application tests, not inferred from Blender QA.

## Materials and provenance

Simple original PBR colors/roughness/metallic values are included. Procedural Blender noise/bump textures are not baked; the browser renderer may add its own original asphalt/sand/water detail.

Original environment geometry: see `assets/environment/LICENSE.txt`. Course geographic geometry derives from OpenStreetMap: **© OpenStreetMap contributors, ODbL**, see `references/route/README.md`. Keep visible attribution in the game and source notices with redistributed route data. Buildings, vegetation, race furniture, road width and elevation are artistic, not a survey.

## Rebuild

```sh
blender -b --factory-startup -t 4 --python blender/export_web_assets.py
# After only course geometry/route data changes:
blender -b --factory-startup -t 4 --python blender/export_web_assets.py -- --course-only
# Terrain + append-only landscaping only, preserving other FBX/GLB binaries:
blender -b --factory-startup -t 4 --python blender/build_course.py -- --terrain-refresh
blender -b --factory-startup -t 4 --python blender/export_web_assets.py -- --terrain-only --stage-only
python3 assets/course/audit_terrain_coverage.py repaired
python3 assets/course/validate_terrain_repair.py
# After successful QA, atomically copy terrain/runtime/manifest into web/public/assets.
blender -b --factory-startup -t 2 --python assets/web/validate_environment_web.py
```
