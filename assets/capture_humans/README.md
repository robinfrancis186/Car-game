# Rigged capture character source

The tested runtime contains exactly two CPO officers and one driver, each using a 53-bone skin. `exports/capture-lod-manifest.json` records exact GLB hashes, texture sizes and measured counts. Near uses the subdivided connected garment; mobile uses its base topology. Shirt, trousers and belt are preserved without edge collapse. The authored skin tint is explicit in all glTF exports.

Reproduce with `blender/build_capture_officer.py` and `blender/export_capture_humans.py` using the existing Blender installation. The source OBJ, morph, joint/weight JSON and unchanged texture pixels are CC0 MakeHuman/MPFB asset data; `source/LICENSE.md`, `source/LICENSE.ASSETS.md` and the two source receipts retain the exact publisher distinction and public URLs/hashes. Data Collection AB, Joel Palmius and Jonas Hauquier (2020) are credited by the skin material. No downloaded Python scripts or MPFB add-on were executed.

The five `*.public.blend` files are editable publication copies. `tools/sanitize_capture_native.py` replaces absolute metadata paths with relative names, without changing any other decompressed bytes. Exact original local authoring files remain preserved outside the committed publication set. Audit: `deployment/capture-native-source-audit.json`.

The original uniform follows Civil Police Officer configuration, printed page16/PDF page19 of the official January2020 Kerala Police uniform manual: https://keralapolice.gov.in/storage/pages/custom/ckFiles/file/SOP-3-KERALA-POLICE-UNIFORMS_compressed.pdf . The PDF and reference photographs are not distributed or reused as textures. No rank stars or SCPO chevrons are added; the crest remains a simplified original approximation.

Validation: 58 aggregate stages, actual desktop/portrait Chrome capture/replay/interruption, 220 grip poses and56 deformed-driver-skin comparisons, with final sampled proximity0.9–5.2mm and no sampled penetration. This is not continuous collision physics or photorealism. Cap/insignia, facial finish, footwear gaps, cuff fit and environment realism remain limited. Phone hardware, Safari and audible audio acceptance are unverified.
