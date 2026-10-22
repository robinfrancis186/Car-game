# Provenance and publication scope

- Game code, interface, procedural Blender geometry/materials, fictional arcade systems and synthesized audio were authored for this project. No purchased/extracted commercial game assets or manufacturer CAD are included.
- Vehicle and Kerala scenery references informed original stylized designs. No reference images, video frames, photo textures, official logos or user-uploaded material are distributed. Original geometry does not imply manufacturer/operator endorsement or clearance of trademark/design rights.
- Coastal route data derives from OpenStreetMap near Kappil–Edava and is adapted artistically. The highland route is authored. Preserve the ODbL attribution/data offer in `references/route/`, `web/public/assets/coastal_map_data.json` and the game UI.
- Public reference sources included Kerala Tourism (`https://www.keralatourism.org/destination/kappil-beach-backwaters-varkala/427/`), Kochi Metro (`https://kochimetro.org/completed-projects/`) and the vehicle manufacturer's Roadster page (`https://www.tesla.com/roadster`). Reference use is not a license to redistribute their photographs, models or marks.
- Runtime dependencies: Three.js 0.170.0 (MIT); Barlow Condensed font (SIL OFL 1.1). Full notices are included at `web/public/vendor/THREE_LICENSE.txt` and `web/public/assets/fonts/OFL.txt`. Build/test dependencies are pinned in the npm lockfile.

## Rights

No new blanket open-source license has been chosen for the original project. `web/package.json` intentionally says `UNLICENSED`; public availability alone is not an added reuse license. Existing scoped CC0 notices for the original environment/transit asset packages are preserved, as are third-party licenses and ODbL attribution. See `LICENSES.md` and individual asset notices. The repository owner can select a broader original-code/assets license separately.

## Clean publication

The release upload excludes user reference media/identifiers, private work notes, research downloads, hosting metadata, credentials, dependency caches, Blender backups, preview renders, generated distributions and historical test/debug reports. Public runtime source/assets are byte-identical to the frozen V10 manifest. Native Blender scene copies use built-in compression with unchanged geometry and portable render-output paths. Reference-filename metadata in two generators and three authoring manifests was anonymized; this does not change generated geometry.
