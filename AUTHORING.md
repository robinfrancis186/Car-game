# Editable Blender sources

Open any `.blend` under `assets/` directly in **Blender 4.3.2 or a compatible later version**. They use Blender's native compression, not a ZIP wrapper. No external models/textures, user reference photographs, external linked libraries or embedded scripts are required to open them.

Main scenes: `assets/car/roadster_concept.blend`, `assets/web/car_web.blend`, `assets/web/car_silver.blend`, `assets/course/Kappil_Coast.blend`, `assets/highlands/Highland_Run.blend`, `assets/environment/Kerala_Coastal_Assets.blend`, and the infrastructure, landscape, foliage and showroom source scenes. `ASSET_SOURCE_MANIFEST.json` lists all 24.

Generators and exporters in `blender/` are normal source scripts. Inspect them before running: they regenerate files and some run CPU renders. Run from a **working copy**, not over a release snapshot. Examples from the repository root:

```sh
blender --background --factory-startup --python blender/build_car.py
blender --background --factory-startup --python blender/export_web_assets.py
```

The committed `web/public/assets/` exports are the exact frozen V10 runtime assets and are ready to use. A complete re-authoring/export pipeline is not a single-command build: generators have ordering dependencies and later refinement/export steps. Existing native sources are the safest starting point for editing. Planning scripts may require Python packages such as NumPy/SciPy; the browser build does not.

`assets/` omits redundant FBX/GLB exports and preview images; frozen runtime GLBs are under `web/public/assets/`. Exporters may recreate working GLB/FBX files under `assets/`. The optional Unreal import scaffold needs those regenerated exports plus a separately installed/licensed compatible Unreal Engine; it has not been compiled or runtime-validated.

The original geometry and materials are procedural project work. The bird-rock runtime texture is an original procedural stone normal map, not a reference photograph. Coast route-derived data retains OpenStreetMap attribution/ODbL obligations. See `LICENSES.md` and `PROVENANCE.md`.
