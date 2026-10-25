# Kerala coastal environment — original prop library

Created in Blender 4.3.2 by `blender/build_environment.py`. All modeled geometry is original procedural work; no third-party mesh, texture or photograph is embedded. These are artistic Kerala-coast-inspired props, not surveyed replicas.

## Files

- `Kerala_Coastal_Assets.blend`: native editable Blender library and presentation scene.
- `exports/<asset>.fbx` and `.glb`: each prop exported separately, root at its intended pivot.
- `manifest.json`: bounds, triangle and mesh counts, material palette, root/mesh names.
- `previews/coastal_asset_preview.png`: CPU Cycles render of the staged asset library. **Not an Unreal screenshot.**
- `previews/KeralaHouse_detail.png`, `CoconutPalm_A_detail.png`, `FishingBoat_detail.png`: inspected detail renders (1100×850).
- `export_validation.json`: actual Blender FBX and GLB re-import checks.
- `QA.md`: tests, visual defects corrected, and remaining limitations.
- `asset_sha256.json`: hashes of final native model, generator, manifest and export files.
- `build.log` / `export_validation.log`: execution evidence.

## Included props

`CoconutPalm_A`, `CoconutPalm_B`, `KeralaHouse`, `FishingBoat`, `RoadReflector`, `RoadSegment`, `BeachSandPatch`, `OceanPatch`, `TropicalGrass`, `SeaWallRock`.

The palms have curved ringed trunks, modeled paired frond leaflets, crown spears and coconut clusters. The house has terracotta tile geometry, ridge caps, lime plaster walls, timber veranda, framed windows/shutters, paneled door and terracotta pots. The fishing boat has a thick hull, gunwales, ribs, seats, floorboards, oars and coir rope.

## Blender use

The `Asset_Library` scene holds originals at the origin in separately named collections. The `Coastal_Preview` scene uses collection instances. Append a named collection into your working scene. Do not append the preview scene when you only want game props.

Meters, +X forward, +Y left, +Z up. FBX uses standard -Z-forward/Y-up export conversion. Preserve root transforms on import; inspect bounds against the manifest. All export modifier stacks have been applied. Asset geometry is mostly closed where relevant; leaves, roofing and ground patches intentionally use surfaces. Use two-sided foliage shading in Unreal.

## Unreal integration status

These exports have been re-imported into Blender, **not imported or run in Unreal** in this cloud environment. Unreal Editor is unavailable here. Collision, LODs, wind, water dynamics and vehicle interaction need in-engine setup and testing. Custom surface meshes do not include authored production UV atlases; use world-aligned materials or unwrap before texture baking. Use simple collision for house/plinth/road and disable collision on thin foliage and decorative roof pieces. Road tiles are 20 m long, 6.6 m paved plus 0.75 m shoulders on either side.

Blender procedural noise/bump nodes are not baked to texture maps and do not transfer through FBX. GLB transfers basic Principled PBR values; reconstruct asphalt/sand/bark/plaster/rock detail in Unreal using the manifest palette and world-aligned noise. The ocean prop is a lightly undulating presentation mesh, not simulated water. No claim of photogrammetry, AAA fidelity, or exact Kerala architectural provenance is made.

## Rebuild and validate

```sh
blender -b --factory-startup -t 4 --python blender/build_environment.py
blender -b --factory-startup -t 2 --python assets/environment/validate_exports.py
```

This particular Blender build has no OpenImageDenoise support, so CPU renders disable denoising explicitly.

## License

Original environment geometry and generated material definitions were created for this project. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. See `LICENSE.txt`. No Tesla marks or third-party licensed content occur in this library.
