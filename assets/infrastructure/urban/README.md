# Kerala-inspired modular urban kit

Original procedural Blender geometry for the **fictional Kerala-inspired v8 district**. These assets are not surveyed reconstructions, and do not imply the Kochi landmarks are located along the real Kappil route. No downloaded model, source photograph, texture image, real business logo or real transit branding is bundled.

## Contents

| GLB basename | Blender width × depth × height | Intended use |
|---|---:|---|
| `KeralaShopRow_A` | 12 × 10 × 10 m | Three ground-floor shutters, striped canopies, six upper balconies, roof tank and stair cap |
| `KeralaShopRow_B` | 10 × 9 × 7 m | Ochre low shop row with terracotta hipped roof |
| `KeralaApartment_A` | 16 × 14 × 25 m | Eight-level pale apartment slab, balcony grid and tile-roof caps |
| `KeralaOffice_A` | 22 × 16 × 18 m | Five-level office, glazed bays, teal sunshades and rooftop equipment |
| `KeralaTeaStall` | 4 × 3 × 3.2 m | Open counter, stools, kettle, cups and generic tea sign |
| `ChineseFishingNet` | 14 × 18 × 12 m | Timber A-frame and cantilever, open sagging grid net, rope and stone counterweights |

- Each native `.blend` contains one named asset collection and root empty matching its GLB basename, ready for collection append/instancing.
- Blender: X facade frontage; **front -Y**, Z up. Exact total envelopes above include awnings, trim and net. The origin is ground-centre.
- GLB: **front +Z**, +Y up, +X frontage. Already converted; do not rotate another 90 degrees around X.
- Each asset is merged into no more than five material meshes/GLB draw primitives. No runtime textures or external URI dependencies.
- Use `urban_assets_manifest.json` for exact bounds, geometry budgets, hashes and provenance. Numeric validation independently reads the GLB payload in `verify_urban_assets.py`.
- Export files are in `assets/web/` and identical copies in `web/public/assets/`. Editable originals are in `native/*.blend`; CPU preview renders in `previews/*.png`.
- Visual meshes only: course integration should supply simplified building colliders. Do not use detailed fishing-net geometry as a road obstacle.

## Rebuild

From project root:

```sh
blender -b --factory-startup -t 4 --python blender/build_urban_props.py
python assets/infrastructure/urban/verify_urban_assets.py
```

The generator writes only these six urban asset names, its native files, previews and dedicated urban manifest. CPU Cycles previews use 16 samples with denoising disabled. The native `.blend` files contain original asset geometry, not the presentation ground/camera/lights.

## Reference use

Primary-source silhouettes were studied, not traced or copied into textures:

- [KMRL official completed-project photographs](https://kochimetro.org/completed-projects/): mixed-height urban context, repeated facade bays, pale surfaces and teal details.
- [Kerala Tourism — Kochi backwaters](https://www.keralatourism.org/kochi/backwaters-kochi.php): contrast between waterfront high-rises and traditional tile-roofed houses.
- [Kerala Tourism — Chinese fishing nets](https://www.keralatourism.org/kochi/chinese-fishing-nets-kochi): timber/bamboo cantilevers, ropes and stone counterweights.

Source photographs remain reference-only outside the playable bundle; references are not a claim that those photos are openly licensed. Generic signs are generated geometry, not third-party artwork.
