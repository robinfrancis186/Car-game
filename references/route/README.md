# Kappil–Edava coastal road source geometry

Retrieved 2026-10-22 directly from OpenStreetMap API:
https://www.openstreetmap.org/api/0.6/map?bbox=76.667,8.769,76.690,8.788

Raw response: `../../research/kappil_osm.xml` (complete ways can extend beyond requested bounding box).

## Files

- `kappil_osm_roads.geojson`: three original road ways with their OSM tags, preserved separately.
- `kappil_osm_route.geojson`: same three connected ways joined, duplicate join nodes removed. A single LineString, 114 nodes, approximately 4,538 metres.
- `kappil_route_local_meters.json`: same nodes converted to local X=east, Y=north, Z=up metres. Origin WGS84 `[longitude, latitude] = [76.6843665, 8.7664547]`. Equirectangular approximation at origin latitude, R=6,371,000 m. Z=0 is a modeling placeholder, NOT measured elevation.
- `kappil_osm_environment.geojson`: OSM coastline, water polygons, building footprints, residential areas and resort boundaries present in the returned map. Source ways are not repaired/merged into multipolygons; do not assume this is a complete land/water surface.

## Real route sequence, south to north

1. https://www.openstreetmap.org/way/473233078 — Varkala–Edava–Kappil Bridge Approach Road, secondary, two lanes, asphalt, two-way, marked lanes according to OSM.
2. https://www.openstreetmap.org/way/239443918 — Kappil Bridge, secondary, two lanes, asphalt, bridge=yes, layer=1. Approximately 116 m long, from `[76.674729, 8.7814491]` to `[76.6736718, 8.7815035]`.
3. https://www.openstreetmap.org/way/250511366 — Paravur–Varkala Road, secondary, two lanes, asphalt.

Northbound: sea generally west/left. Edava–Nadayara backwater east/right around the bridge. Route is NOT a closed loop. Any closure/return road, widening, ramps, race barriers, traffic pacing or elevation are fictional design changes and must be labeled as such. This is an approximate public map centerline, not survey/CAD evidence. Data does not establish current road condition, exact lane widths or racing safety.

## License / attribution

Map data © OpenStreetMap contributors, available under Open Database License (ODbL) 1.0.
https://www.openstreetmap.org/copyright
https://opendatacommons.org/licenses/odbl/1-0/
https://osmfoundation.org/wiki/Licence/Attribution_Guidelines

Keep this credit with distributed geometry, and use readable in-game/source credits such as:
`Road geometry: © OpenStreetMap contributors (ODbL 1.0). Adapted for a fictional closed-course game.`
Link OpenStreetMap to its copyright page. Preserve availability of the ODbL-derived geometry/database and record transformations; do not relabel this geometry as CC0 or entirely original. Original game code and wholly independent assets should have their own clearly separated notices.

## Official setting references

Kerala Tourism: https://www.keralatourism.org/destination/kappil-beach-backwaters-varkala/427/
Kollam District Tourism Promotion Council: https://www.dtpckollam.com/destination/kappil-beach
Official photo brochure: https://www.keralatourism.org/images/ebooks/pdf/trivandrum_kollam_ebrochure.pdf

Use scenery cues rather than the copyrighted brochure image as a game texture: coconut groves, golden sand, grey shoreline rocks, ocean swell on the west, quieter jade-green backwater on the east, small boats, bridge railings, and sparse low-rise coastal buildings. Houses, shops, scooters, buses and autorickshaws can be original representative art; actual traffic counts and building heights were not verified.
