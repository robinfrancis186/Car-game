# Original Kerala-inspired houseboat

A compact scenic houseboat authored procedurally in Blender, from visual study of the two user-supplied backwater references. It is **not** a surveyed replica or a claim that this vessel exists near the original Kappil road.

## Files and integration

- GLB: `assets/web/KeralaHouseboat.glb`; identical runtime copy in `web/public/assets/`.
- Native: `KeralaHouseboat.blend`, containing named collection and root empty `KeralaHouseboat`.
- Source: `blender/build_houseboat.py`.
- `houseboat_manifest.json`: exact bounds, axis/pivot contract, checksum, counts and provenance.
- `binary_validation.json`: independent standard-library parsing of actual exported GLB buffers.
- `KeralaHouseboat_preview.png`: inspected **Blender CPU asset render**, not an in-game screenshot. The presentation water plane is not part of the exported asset.

Blender **+X forward, +Z up**; GLB **+X forward, +Y up**. Root origin is at waterline zero; the hull extends 0.75 m below it. Overall length is about 18.07 m, beam 5.24 m, and maximum canopy is 5.82 m above water. Keep the hull in a water area at least 0.75 m deep. The model is scenery only and carries no gameplay collider or physics simulation.

Four merged material meshes: dark hull/windows, bamboo/timber, tan thatch, cream trim/fenders. Total **4,812 triangles**, **4 draw primitives**, and **260,220 bytes**. Geometry only: no image texture, downloaded model, real logo or copied vessel lettering. The referenced photographs remain study-only in the separate reference folder and must remain excluded from playable packages.

## Visual QA

Inspected the finished 24-sample CPU Cycles preview with denoising off: tapered dark hull reads as a boat; shallow arched cabin roof, separate veranda canopies and upper viewing deck remain distinct; repeated windows are framed, side bamboo strips align, ring fender holes are open and the waterline hides the submerged keel correctly. Porches have posts, rails and benches. No camera clipping, opaque net/photo planes or missing materials observed.

## Rebuild and verify

From project root:

```sh
blender -b --factory-startup -t 4 --python blender/build_houseboat.py
python assets/infrastructure/backwater/verify_houseboat.py
```

Independent payload checks passed: finite binary positions/normals, no degenerate triangles, exact manifest bounds, identity node transforms, embedded-only buffers, no image dependencies, checksum match and identical public copy.
