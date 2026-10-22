# Original service/showroom bay

Menu-only presentation asset, not part of either race course. Editable source: `ServiceShowroomBay.blend`, collection `ServiceShowroomBay`. Generator: `blender/build_service_showroom.py`. GLB staged and public copies match.

- 18 ×14 m footprint, Three X ±9 / Z ±7. Open front faces +Z.
- Floor and inspection stage top are both exactly Y=0; stage radius 3.35 m. The floor has an actual circular opening around the stage, not overlapping coplanar faces.
- Six materials, 8,562 triangles. Original beveled cabinets/drawers/handles, pegboard/tools, sectional garage door, structural I-beams, ceiling strips, circular inspection lighting, floor joints/grates, safety markings and open cable coils.
- No embedded car, cameras or lights in the GLB. `ServiceShowroomBay_Preview.blend` includes the existing silver car and explicit preview lighting only.
- Emissive strips are visible design geometry, not a substitute for actual scene lights. Suggested anchors and accepted front-view hero cameras are in `showroom_manifest.json`.
- CPU actual-GLB ray QA proves 16 hero sightlines clear and five stage heights at Y=0. Actual buffer QA: finite geometry/normals, no degenerates, no external buffers/images. Evidence: `assets/foliage_detail/aux_art_validation.json`; runner: `blender/validate_aux_art.py`.
- Original project geometry and palette; no supplied/reference photos, downloaded textures or third-party model geometry are shipped. Text uses Blender's bundled font converted into geometry.

## Preview honesty
`ServiceShowroomBay_preview.png` and `ServiceShowroomBay_overview.png` are CPU Blender renders of the actual exported design, not browser screenshots. The installed Blender build explicitly reports "Failed to denoise, build has no OpenImageDenoise support"; no blur/filter or false denoising claim is used. `ServiceShowroomBay_preview_final.png` is the higher-sample adaptive CPU view (192 maximum samples) when complete. GPU browser appearance and performance remain renderer/browser QA responsibilities.
