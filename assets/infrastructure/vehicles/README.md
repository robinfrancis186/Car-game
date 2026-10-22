# Original coastal transit vehicles — v8

Two Blender-authored scenic vehicles, inspired by inspected official Kochi Metro / Water Metro photographs. **Approximate original interpretations, not operator CAD, exact replicas or endorsed vehicles.** Generic names only; no operator logos, downloaded meshes or photo textures.

## Deliverables

| Asset | Geometry budget | Root / placement |
|---|---:|---|
| `assets/web/coast_metro_train.glb` | 13,500 triangles; 9 material draws | `CoastMetroTrain`; rail contact at Y=0 |
| `assets/web/water_transit_ferry.glb` | 9,724 triangles; 3 material draws | `WaterTransitFerry`; sea level at Y=0 |

- `transit_vehicles.blend`: editable original geometry and individually named components. Separate collections; ferry is displayed 18 m alongside the train for editing. This source layout offset is **not** in the exported ferry.
- `../../../blender/build_transit_vehicles.py`: reproducible procedural generator, exports, validation and studio renders.
- `transit_vehicle_manifest.json`: convenient runtime API; identical staged copy in `assets/web/`.
- Individual `*_manifest.json`: exact bounds, dimensions, SHA-256 hashes and material names.
- `*_preview.blend`: actual GLB reimport with studio presentation, not a more detailed substitute.

## Runtime contract

Meters; glTF **+X forward, +Y up, -Z left**. Identity root placement except the runtime course transform. No textures or network dependencies.

### Train

Three independent carriage pivots: `TrainCar_0`, `TrainCar_1`, `TrainCar_2`; original center offsets **[+19.4, 0, -19.4] m**. Place and orient each at its own sampled point on the route. The last carriage's source local Y rotation is **-PI** so its cab points backward: preserve/add that rotation to the path tangent, do not replace it with the forward carriage yaw. Both ends are cabs; a reversing shuttle need not rotate the whole train 180 degrees.

Overall bounds approximately **57.66 m long × 2.962 m wide × 4.214 m high**. Platform sill ~1.15 m above rail. Each carriage combines geometry into three vertex-colored PBR groups. Dark corrugated end collars are split between cars for modest curve articulation; they are not deformable cloth. Wheels, doors and bogies are modeled but not individually animated in this scenic LOD. Opaque glazing and no complete passenger interior.

### Ferry

Approximately **23.855 m long × 8.42 m wide** including fenders; roof/mast reaches **6.23 m above sea level**, twin hull draft **1.12 m**. Passenger deck Y≈1.09 m. Open stern occupies local X approximately -11.65 to -8.7 m; squared open bow deck is ahead of the raised pilot house. Manifest supplies stern port/starboard wake sockets. Move root rigidly; restrained heave/roll is possible. No naval dynamics, operating boarding gate or complete saloon interior is claimed.

### Materials

`Transit_Surface`, `Transit_Glazing`, `Transit_Lamps`. Preserve glTF vertex colors. Palette variation is authored per corner to limit draw calls; painting the material globally changes all surfaces sharing it. `Transit_Lamps` supports optional emission intensity changes, but does not itself cast point lights in Three.

## Final part previews

- `coast_metro_train_preview_cab.png`: close cab, doors, bogies and end collar.
- `coast_metro_train_preview_front.png`: complete three-car consist.
- `water_transit_ferry_reference_refined_front.png`: reference-corrected raised pilot house, pink diagonal pillar, squared twin-hull bow and lifebuoys.
- `water_transit_ferry_reference_refined_stern.png`: long saloon glazing, original wave ribbons and open rear deck/canopy.

1440×900 CPU Cycles renders, 64 samples, no supported denoiser. These are inspected **asset previews**, not gameplay captures. The train glass may reflect bright illumination like any PBR surface; its actual dark glass geometry is projected over the sloped shell, not buried within it.

## Verification

`coast_metro_train_validation.json`, `water_transit_ferry_validation.json`: actual Blender GLB round trips, finite geometry and budgets: **PASS**.

`three_validation.json`: actual Three.js GLTFLoader parses, vertex colors, no textures, triangle/draw limits, carriage centers/independence/rear-facing cab, train ground contact, ferry origin and submerged hull: **PASS**. Test runner: `node assets/infrastructure/vehicles/validate_transit_three.mjs` from project root. No rendered browser integration or animation quality is implied by these asset-level tests.

## Rebuild

```sh
blender -b --factory-startup -t 4 --python blender/build_transit_vehicles.py
node assets/infrastructure/vehicles/validate_transit_three.mjs
```

Set `TRANSIT_SKIP_RENDER=1` to rebuild assets and validation without rendering. Set `TRANSIT_FERRY_ONLY=1` for ferry-only rebuilds, preserving the train GLB byte-for-byte. Set `TRANSIT_TRAIN_ONLY=1` for train-only rebuilds, preserving the ferry GLB byte-for-byte. Generator writes only vehicle outputs and the two staged GLBs / transit API manifest; it does not modify course geometry, game JavaScript or public staging.

## References and packaging

- [Kochi Metro official completed projects photographs](https://kochimetro.org/completed-projects/): three silver coaches, turquoise rounded cab face, dark windows and door rhythm.
- [Water Metro official ferry photograph](https://cdn-dev.watermetro.co.in/boat_05_b6ae163381.png): low white cabin, tall dark windows, blue/cyan graphics, narrow purple stripe and open stern canopy.

Reference pixels were inspected locally. No source photograph is embedded in an asset or browser bundle. `references/transit/` is a private working reference cache, **not part of this deliverable: exclude it from redistributed source archives**. The original mesh kit and original rendered previews are in this folder. Transit agency trademarks/design rights are not represented as licensed by these original interpretations.

## Ferry reference revision 2

The user supplied clear side/bow photos (`478E3E5E-FF77-4411-B019-E083D958BFE2.jpeg`, `A6C5C820-A33E-41A5-9AB1-30781FBFFE90.png`). Their pixels were inspected, and the first generic low-cabin ferry was replaced. Revision 2 has separated purple twin pontoons, an open squared foredeck, four orange/white lifebuoys, a raised blue forward-leaning pilot house, a physical magenta diagonal pillar, continuous stepped saloon glazing, original layered cyan wave ribbons, crew/passenger doors, deck rails, roof equipment and an open stern canopy. The train asset was held unchanged during the ferry-only revision; the later independently audited gauge correction is documented below. No official marks or supplied photos are embedded.

`history_v1/` preserves the obsolete generic mesh/render evidence; it is not the active asset. Earlier `water_transit_ferry_preview_*.png` files are superseded by `water_transit_ferry_reference_refined_*.png`.

Actual exported local bounds: min **[-12.005, -1.12, -4.21]**, max **[11.85, 6.23, 4.21]** (Three XYZ, meters). Recommended conservative OBB center **[-0.0775, 2.555, 0]**, half-extents **[11.9275, 3.675, 4.21]**. This includes mast/fenders; a capsule fitted only to total length/beam misses squared bow corners. Exact values are in both manifests.

`ferry_reference_revision_validation.json`: actual GLB ray checks confirm an empty central channel below the bow deck and two separate pontoon hits. Source checks confirm four patterned lifebuoys/two structural pink pillars. Train SHA-256 is checked against the current manifest. Node/Blender asset tests are not live game collision or water simulation tests.

## Integrated train gauge correction

Independent actual-GLB integration QA found that the initial train wheel centers (±0.94 m) did not overlap the viaduct's 1.435 m-gauge rail tops. The source and exported wheels were moved inward to **±0.7175 m**; the outer metal rim centers moved to **±0.8075 m**. Wheel radius remains 0.39 m, contact width 0.16 m, rail-contact Y=0. No track widening was performed.

`train_gauge_validation.json` **PASS** reads both actual `coast_metro_train.glb` and `MetroViaductSpan.glb`: all **24** wheel contact bands |Z|=0.6375–0.7975 fully cover the measured rail-top bands |Z|=0.680–0.755, with **0.075 m overlap** per wheel. Body geometry above the wheels, carriage centers and rear base yaw match the pre-correction asset. The ferry remains byte-identical. This is straight-contact geometry verification, not a continuous curved-track dynamics simulation.

Run `node assets/infrastructure/vehicles/validate_train_gauge.mjs`. The immutable comparison asset is in `history_gauge/`. Native source and the train preview studio scene contain the corrected gauge. Existing train PNGs predate this small undercarriage correction; body appearance is unchanged and they were not expensively rerendered.
