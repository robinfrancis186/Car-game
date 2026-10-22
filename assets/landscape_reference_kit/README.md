# Original landscape reference kit — v9

Three original scenic assets built as individually editable parts in Blender 4.3.2. The two user reference photographs were visually inspected; no photographs, official logos, downloaded meshes, are embedded in these assets. One small original procedural stone normal map is embedded only in the bird GLB. The monumental bird is an original stylized guardian interpretation, **not a measured replica of Jatayu**. The tree is a broadleaf/rain-tree-like scenic interpretation, not a botanically exact specimen.

## Deliverables

| Asset | Native source / preview | Runtime GLB | Triangles | Draws |
|---|---|---|---:|---:|
| BirdRockLookout | `BirdRockLookout.blend` / `BirdRockLookout_preview.png` | `../web/BirdRockLookout.glb` | 17,550 | 3 |
| CanalShikara | `CanalShikara.blend` / `CanalShikara_preview.png` | `../web/CanalShikara.glb` | 7,320 | 3 |
| CanalRainTree | `CanalRainTree.blend` / `CanalRainTree_preview.png` | `../web/CanalRainTree.glb` | 13,856 | 2 |

All preview PNGs are CPU Cycles renders of the **actual reimported runtime GLB**, 1440×1000, 48 samples, no denoising. The corresponding `_preview.blend` files contain neutral presentation ground, lights and a camera; these are not part of the runtime GLB. Source `.blend` files contain the asset at its own root, not the presentation scene.

## Coordinate and placement contract

- Meters, Blender +X forward/head/arch direction, +Y left, +Z up.
- glTF/Three +X forward, +Y up, -Z left. Root position0, scale1.
- Root names exactly match the asset basenames. Tree/landmark roots are at ground; boat root at waterline.
- Individual JSON manifests record authoritative bounds, full SHA-256, materials and collision proxies in **Three local coordinates**.
- Bird foot is approximately58×49m with total height20.1m. Rock-only OBB is computed from all exported rock vertices; separate simplified bird body/neck/beak proxies supplied. Thin outer feather tips remain scenic.
- Tree crown extends roughly29m across and leaf geometry begins above9m at full scale. Put trunk outside the road/canal; rotate the +X arch toward water. Existing `RainTree_Leaf` material matches the runtime `/leaf|frond|grass/i` wind hook. It uses root-local height and subtle0.07m wind; leaves are non-solid. Two trunk capsules and a buttress-root OBB are supplied; minor lateral branches are scenic.
- Shikara is an8.34m open narrow canopy boat. Draft~0.63m, canopy top~2.56m. Full conservative OBB includes the stowed oar. Generic six-seat interior; no people, complete controls or marine simulation.
- Base surface colors use vertex colors. The bird also embeds one original256×256 periodic procedural stone micro-normal PNG, generated mathematically in the Blender build (no photograph input). Surface colors should not be replaced with flat white materials.

## Validation

Run from the project directory:

```sh
node assets/landscape_reference_kit/validate_landscape_kit.mjs
```

`three_validation.json` records actual Three GLTFLoader parsing, finite vertices, vertex colors, root transform, dimensions/hash agreement, no albedo photo textures, one original bird normal map, mesh budgets, canopy clearance/wind material recognition, all exported rock vertices inside rock OBB, and complete boat bounds inside its OBB. Node validates PNG dimensions/material wiring with an image-bitmap shim; actual texture pixels are decoded and visually checked in Blender roundtrip renders. This is **not browser gameplay or collision-dynamics proof**; route placement, continuous driving/flight and rendered browser tests are owned by game integration.

## Rebuild

```sh
blender -b --factory-startup -t 2 --python blender/build_landscape_reference_kit.py
# A single part; omit KIT_SKIP_RENDER to render its actualGLB preview:
KIT_ONLY=CanalRainTree KIT_SKIP_RENDER=1 blender -b --factory-startup -t 2 --python blender/build_landscape_reference_kit.py
```

The generator creates the original editable source, optimized per-material meshes, GLBs, manifests and preview scenes. Do not include `references/` photographs in redistributable project archives. All mesh and palette content in this kit was authored for this project.
