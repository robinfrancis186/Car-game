# V8 Kerala infrastructure / Blender assets

This is an original, fictional Kochi-inspired urban/coastal remix on the existing OSM-derived Kappil route. It is **not** an accurate map of Kochi or an official Metro/Water Metro service. Marine Drive is pedestrian-only; the fictional race roadway runs alongside an inspired promenade, not on that real promenade.

## Integrated scene

- 4,539.752 m horizontal route, 1,525 samples; planar coordinates are bit-for-bit unchanged from the preserved v7 route.
- 1,841 static prop instances, including 477 new district placements. 174 old props intersecting the new authored blocks were removed.
- Five districts: Coastal Villages, Metro Market, Skyline Flyover, Backwater Quarter, Harbour Avenue.
- New kit placements: 12 metro viaduct spans, one station, one terminal, two promenade segments, 32 access-street segments; 90 shop-B / 64 shop-A / 44 tea stalls / 37 apartments / 20 offices; 118 lamps and 54 palms; one fishing net and one original houseboat.
- Buildings use coherent cream, terracotta, pale-blue and muted-ochre per-block facade/accent metadata. Geometry remains shared for runtime instancing.
- Two dynamic transit configurations: a 300 m elevated metro alignment at rail-contact Y=13 m and a 160 m backwater ferry shuttle. Both use ping-pong motion with dwell, not closed-loop teleport paths. Runtime vehicle movement is implemented separately by the game renderer.
- Static houseboat footprint is fully in mapped water. Ferry route cross-section checks are water-only. The fishing-net foundation is dry while its suspended net faces actual water.

## Road elevation and collision

The base road is Y=.18 m. Smoothstep ramps rise over s2480–2630 to **absolute Y=10.00 m**, remain level until s2860 and descend to base by s3010. Planar route and horizontal progress distance are unchanged. Maximum designed grade is approximately 9.82%.

Asphalt half-width 3.6 m; shoulder 4.6 m; slab half-width 4.8 m. The closed slab top is roadY-.10 and bottom roadY-.65. Edge barriers are centered at ±4.42 m, .30 m thick, 1.10 m tall including the metal rail. Road, markings, reflectors, lamps, checkpoint coordinates and authored gate structures are raised consistently.

- `elevated_corridors` describes continuous drivable deck / underside / edge physics, avoiding a chain of round rail bumps.
- `infrastructure_colliders.json`: 455 OBBs for building footprints, structures, piers, poles, moored houseboat and four fishing-net foundation posts.
- `furniture_colliders.json`: 105 OBBs plus four long bridge-rail capsules.
- OBB heading is atan2(+Z,+X), negative Blender yaw. `y` is the bottom elevation, not the center. The renderer yaw remains the same positive angle as Blender +Z yaw after coordinate conversion.
- `districts`, `transit_routes`, and `collision_file` are at the runtime JSON root for the game loader; descriptive copies also remain under `world`.

## Original modules and budgets

| Module | Triangles | Material draws | GLB bytes |
|---|---:|---:|---:|
| MetroViaductSpan | 624 | 4 | 39,728 |
| MetroStation | 6,028 | 5 | 316,972 |
| WaterTransitTerminal | 2,557 | 5 | 143,584 |
| PromenadeSegment | 1,144 | 5 | 74,016 |
| Streetlight | 116 | 3 | 9,496 |
| SideStreetSegment | 108 | 3 | 8,580 |

These six architecture modules total 592,376 bytes / 10,577 triangles. The station has a silver curved barrel roof, cyan edge rim, enclosed glazed body, open train portals, platform, concrete piers and switchback stair. The terminal uses a broad terracotta roof, repeated gables, cream walls, sheltered boarding pontoon and gangway.

Urban module details are in `urban/urban_assets_manifest.json`; train/ferry in `vehicles/` and `assets/web/transit_vehicle_manifest.json`; houseboat in `backwater/houseboat_manifest.json`. The train wheel/rail gauge validation is in `vehicles/train_gauge_validation.json`.

## Sources and rights

All shipped infrastructure, urban modules, vehicles and houseboat geometry is original procedural Blender work. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. No external model geometry, logos or photo textures are shipped in the runtime. Official architecture references are listed in `research/KERALA_INFRASTRUCTURE_REFERENCES.md`; user-provided photographs informed silhouette revisions and are kept only as project reference material.

Route, coastline and water geometry remain derived from OpenStreetMap: **© OpenStreetMap contributors**, ODbL. See `references/route/README.md`. Artistic elevation, road widths, transit alignments, buildings and race furniture are not survey data.

## Verification and reproducibility

`tests/validate_v8_infrastructure.py` generates `tests/v8_infrastructure_qa.json`, including source/export SHA-256 hashes. Final run passes:

- Six architecture GLBs: finite vertices/normals, zero degenerate triangles, ≤5 draws each, public copies identical.
- 687 graded-road vertical rays: all hit, maximum analytical-profile deviation 3.13 mm.
- 412 slab top/bottom checks: maximum deviation 6.62 mm.
- 4,570 new building footprint probes: all dry land.
- 243 ferry route/beam probes: all mapped water.
- Fishing net: nine dry foundation probes and 25 wet suspended-net probes.
- Root runtime schema and final train/ferry/houseboat public copies checked.

These are static geometry/placement tests, **not** WebGL, gameplay, performance or visual acceptance claims. Gameplay and independent audits are recorded separately.

Build order from project root:

```sh
blender -b --factory-startup -t 4 --python blender/build_transit_infrastructure.py
# Urban, transit-vehicle and houseboat generators have separate source scripts/manifests.
python blender/plan_v8_districts.py
blender -b --factory-startup -t 4 --python blender/build_course.py
blender -b --factory-startup -t 4 --python blender/export_web_assets.py -- --course-only
blender -b --factory-startup -t 4 --python blender/export_furniture_colliders.py
python tests/validate_v8_infrastructure.py
blender -b --factory-startup -t 2 --python blender/render_v8_districts.py
```

`sync_v8_final_details.py` records the final in-place native fishing-net/text-cap correction; a full rebuild already consumes the corrected layout and cleaned architecture sources.

Integrated preview paths: `renders/v8_districts/{MetroMarket_Integrated,FlyoverApproach_Integrated,BackwaterQuarter_Integrated}.png`. These are clearly labeled Blender CPU art-direction renders, not game screenshots. This Blender binary has no supported denoiser (explicit OpenImageDenoise enum probe failed); final renders use 64 samples. Runtime water, sky, textures, shadows and animated transit are implemented separately and can look different.

## Independent final audit

Archived unchanged at `tests/independent_v8/kerala_v8_independent_audit.md`, with reproducible harnesses and JSON. All 455 infrastructure proxies pass; 2,724 actual GLTFLoader road rays have no gaps; 207 upward deck-underface rays verify the full .65 m offset and downward normals. The independent ferry cycle check contains 52,624 discrete actual-water vertex/time ray samples with no dry misses (not a continuous swept-volume proof). The actual loader parses 29 GLBs, 1,841 props, two transits and five districts under a stubbed GPU renderer. Final independent 74-test gameplay rerun passes, including six automated graded-route runs with zero damage. Actual browser/Mac play remains a separate acceptance gate.
