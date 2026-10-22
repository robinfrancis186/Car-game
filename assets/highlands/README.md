# Highland Run — original Blender / browser course

This is a **fictional Kerala-inspired hill course**, not a surveyed real road or a relocation of the coastal OSM map. User-supplied photographs informed the tea planting, winding mountain-road composition and NH66-style divided carriageways. No photograph textures or third-party geometry are shipped in the runtime.

## Implemented world

- 3,758.13 m horizontal route, 1,254 samples; asphalt climbs from 0.18 m to 100.18 m. Maximum actual grid-supported road grade: **5.330%**.
- Three broad genuine switchbacks/turnbacks, not a flat road with painted mountain scenery.
- First 760 m: two three-lane carriageways, a real planted median and black/yellow kerbs/outer barriers. A broad 60 m junction connects them before the estate road.
- 480 original, closed, three-dimensional contour-following tea rows; combined planting length 146.38 km. Denser contour intervals are used on gently sloping plots. Low tea planting is scenic/non-colliding; tree trunks and other major solids have proxies.
- 470 low-poly original shade trees, 68 original coconut palms, five small shop modules, four estate tea stalls, an original exit gantry, and the original BirdRockLookout landmark.
- Bird Rock Ridge is a separate 78×78 m terrain plateau at 100 m. The landmark is an artistic reclining-bird interpretation, not an exact sculpture replica.
- Four Explore districts are available independently: Divided Highway, Lower Tea Bends, Estate Switchbacks, Bird Rock Ridge.

## Native sources and reproducibility

1. `blender/plan_highlands.py`: deterministic route and exact height grid (NumPy/SciPy).
2. `blender/plan_highland_tea.py`: extracts contour rows from actual terrain triangles, smooths their plan paths, then resamples their bases on the same surface.
3. `blender/build_highland_props.py`: original shade tree and directional gantry source/export.
4. `blender/build_highlands.py`: native assembly, road/furniture/tea meshes, placements, collision proxies and runtime export.
5. `blender/validate_highlands.py`: actual binary GLB geometry/grid/road audit.
6. `blender/render_highlands.py`: CPU art-direction evidence renders of the actual source scene, not browser/FPS evidence.

Editable source: `assets/highlands/Highland_Run.blend`; prop library: `assets/highlands/Highland_Props.blend`. Every road, hedge, rail, median and terrain part is original procedural Blender mesh geometry. Reused environment and urban modules retain their separate original source libraries. BirdRockLookout source/proxy provenance is in `assets/landscape_reference_kit/BirdRockLookout_manifest.json`.

## Runtime contract

- Load `course_runtime_highlands.json`, not the coastal `course_runtime.json`.
- Runtime coordinates: Three X east, Y up, Z south; Blender `[x,y,z]` becomes `[x,z,-y]`.
- `terrain_grid`: origin in world X/Z, step `[8,8]`, count `[351,301]`, row-major heights, diagonal `sw-ne` (00–11). Use **triangle**, not bilinear, interpolation. All 210,000 grid triangles match the exported terrain; the additional 8 triangles are a flat 0 m horizon apron to ±6 km.
- Asphalt is at route Y. Shoulder height drops linearly by 0.06 m. Highway strip offsets 0/+14 m are relative to Three route-right `[-tz,tx]`.
- Earth-supported hill roads have **no elevated corridor**. Ground flight/landing must use the heightfield rather than a flat 0 m floor.
- `collision_file`: `highlands_infrastructure_colliders.json` (486 proxies: 484 OBBs, two bird capsules).
- `furniture_file`: `highlands_furniture_colliders.json` (1,110 continuous median, highway-edge and hill-rail capsules). These are not circle-bead barriers.
- Existing palm trunk proxies add 68 more gameplay obstacles, yielding 1,664 total runtime proxies.
- District, event, road-section, garage, Explore and collision fields are at the JSON root. No transit or ocean mesh is implied.

## Optimized geometry

Four static course GLBs contain 558,670 triangles / 12,794,112 bytes total, split into 294 material/spatial mesh nodes (256 m cells) for independent frustum culling. Materials remain shared. This is the whole-course count, not a claim about triangles drawn in a frame. ShadeTree: 1,128 triangles / two draws / 28,136 bytes. Gantry: 952 triangles / three draws / 44,588 bytes. BirdRock, palms and buildings have their own manifests. GPU performance requires real browser measurement.

## QA evidence

`tests/highlands_geometry_qa.json` records final source hashes and checks:
- 3,390/3,390 actual GLB asphalt coverage queries across both highway strips and hill-road edges; maximum height discrepancy 5.52 mm.
- All 210,000 terrain triangle centers agree with the exact runtime grid within 7.5 micrometres.
- No downward terrain faces, zero-area triangles, non-finite vertex/normal data, or missing prop GLBs in the inspected exports.
- Source and public copies are byte-identical.

Gameplay worker reported six event/car completions with zero damage, four safe district starts/recoveries, opposing-carriageway/median tests and 24 varied hillside landings. Those are automated model tests, not human-play, WebGL performance or visual acceptance claims. Independent audit and actual browser checks are recorded separately by their owners.

## License / reference boundary

New procedural geometry and scripts are dedicated CC0. User photographs are visual references only, not redistributed as game textures. The track is not real NH66, a real tea estate or the exact Jatayu sculpture. No real infrastructure operator endorsement is implied. Existing project asset licenses and coastal OSM attribution remain in their own source manifests; no OSM geometry is used for this fictional Highland route.
