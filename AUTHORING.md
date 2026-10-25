# Editable game sources

The repository includes **45 native Blender scenes** under `assets/`, plus the generator/export/validation scripts in `blender/` and asset subfolders. Open scenes in Blender 4.3.2 or a compatible later version. `ASSET_SOURCE_MANIFEST.json` lists current hashes; the original V10 publication receipts remain under `docs/provenance/v10/`.

23 of the original 24 Blender scenes are byte-identical to V10, the silver-car scene reflects its later authored update, and 21 additional native scenes cover the newer cars, showroom variants, gameplay props, aircraft, ramps and surface-test route. All 45 were reopened read-only with script execution disabled: no linked libraries, embedded text scripts, private-reference identifiers or secret-bearing metadata were found. A few scenes pack original procedural normal/roughness images; these are authored textures, not user reference photographs.

Work in a copy before running generators: they can overwrite assets and render outputs. The browser uses the frozen `web/public/assets/` exports; no Blender installation is needed to play or build the browser package. Full re-authoring is not a single-command pipeline: generators have ordering dependencies and later refinement/export steps. Planning tools may also need NumPy/SciPy. Preserve manifests, procedural textures and route data when editing.

`assets/` retains authoring exports, source scenes, manifests, validation evidence and required textures. Redundant rendered previews are omitted. `assets/showroom/*before*` and other baseline scenes are historical authoring checkpoints, not current browser scene definitions. The current coastal pavilion is authored in `web/src/showroom-scene.js`; its optional proof renderer lives in `tools/scene-proof-r3/`.

The inherited `unreal/` scaffold remains for continuity; it is not the current browser implementation, is not compiled or runtime-validated here, and requires a separately installed/licensed compatible Unreal Engine. See `LICENSES.md` for source and third-party rights.
