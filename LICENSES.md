# Attribution and rights

Original project code, headless adapters, manual clients and procedural/world data were authored for this project. No new blanket open-source license is granted here; `package.json` intentionally remains `UNLICENSED`.

## OpenStreetMap-derived data

© OpenStreetMap contributors. OSM source/derived coastal data are provided under the Open Database License (ODbL) 1.0. Preserve the attribution and database offer in `data/coastal_map_data.json`, exposed by the server at `/map-data`.

- https://www.openstreetmap.org/copyright
- https://opendatacommons.org/licenses/odbl/1-0/

The Highland route and exported water/scene authoring are identified in source provenance. Artistic alterations do not remove ODbL obligations from the underlying coastal database.

## Runtime dependency

`ws` 8.22.0 — MIT License. Full notice: `docs/WS-LICENSE.txt`. The dependency is pinned in the lockfile; it is installed by npm, not vendored in this branch. No optional native accelerator or install script is required.

`docs/V10-LICENSES.md` preserves the inherited project's broader historical notice. Paths there refer to the V10 `main` branch. This server/Canvas diagnostic does not ship the 3D renderer, Blender scenes or font listed in that historical notice. No user/reference photographs, commercial meshes or manufacturer logos are distributed, and no manufacturer/transit-operator endorsement is implied.
