# Original authored airtime decks

The two editable Blender wedges use the same metre-scale centerline sampling and linear rise as the deterministic game model. Exports are world-positioned, +Y-up glTF with five material draws and 328 triangles each. Existing road meshes/elevations remain unchanged. The model, not a whole-course convex collision hull, handles support, sidewalls, lip departure and landing.

`Coast_AirtimeRamp_preview.png` and `Highland_AirtimeRamp_preview.png` are Blender CPU part previews with a short neutral road context. They are not gameplay screenshots or final integrated-world visual acceptance. Runtime asphalt uses the original shared micro-normal/roughness and grain treatment. White forward chevrons, hazard lip paint and yellow landing-edge dashes are original geometry, not copied images.

Generator: `blender/build_airtime_ramps.py`. Idempotent metadata integration: `tools/integrate_v15_airtime.py`. Actual exported support validation: `web/tests/ramp-geometry.test.mjs`.

The coastal location derives from the attributed OpenStreetMap centerline; preserve the project's ODbL notices and map-data availability. The ramp geometry and Highland location are authored. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. No video or uploaded reference image is included.
