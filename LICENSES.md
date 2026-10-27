# Distribution notices

## Original project work
The original project code, procedural Blender generators, vehicle/environment geometry, parameterized materials, audio synthesis and interface were created for this project; no purchased or extracted commercial game models, textures, sounds, logos or Need for Speed assets are included. See individual asset README files for authoring scope and limitations. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.

A Roadster-inspired design and Tesla references do not imply trademark, design-right or manufacturer permission/endorsement. No manufacturer CAD is supplied. Reference photographs/HTML in research and user-reference directories are for study only and are excluded from playable distributions.

## OpenStreetMap
© OpenStreetMap contributors. Route/environment source data are available under the Open Database License (ODbL) 1.0: https://www.openstreetmap.org/copyright and https://opendatacommons.org/licenses/odbl/1-0/ . The OSM-derived route/database and its provenance are included in `references/route/`; preserve this notice and the in-game attribution. Artistic smoothing, flattening and scenery do not make the original route database CC0. The course is a produced work, with the derived data provided separately.

## Three.js 0.170.0
MIT license, copyright © 2010–2024 three.js authors. Full text: `web/public/vendor/THREE_LICENSE.txt`. Pinned official package source: https://www.npmjs.com/package/three/v/0.170.0 . GLTFLoader, BufferGeometryUtils and RoomEnvironment are from the same official package/license.

## Barlow Condensed
Barlow Condensed Black Italic, SIL Open Font License 1.1. Full notice and license: `web/public/assets/fonts/OFL.txt`. Official Google Fonts repository: https://github.com/google/fonts/tree/main/ofl/barlowcondensed . Embedded in the offline HTML without modification.

## Build/test dependencies
esbuild 0.25.11 (MIT), Playwright Test 1.58.2 (Apache-2.0), installed through their official npm packages. They are development tooling, not required by or shipped as game runtime dependencies. Blender-generated assets can be used separately from Blender under their own stated terms. No Unreal Engine binaries are distributed.

## V8 Kerala infrastructure
Original modeled metro train, catamaran ferry, station, terminal, urban kit and related scenery use silhouette/material cues from publicly viewed official and user-supplied reference images. No operator logos, downloaded meshes, reference photographs, video frames or photo textures are game assets. Source references and distinctions are documented in `research/KERALA_INFRASTRUCTURE_REFERENCES.md`. Fictional branding and placements do not imply affiliation with transit operators.

## V9 authored landscapes and map-data offer
The Highland course, bird-rock sculpture, broadleaf tree, shikara and procedural stone micro-normal map are original project work, not copied reference textures. The garage Map data link offers the original OSM-derived source records, projection/provenance and smoothed coastal centerline as a downloadable JSON database under ODbL. This file is embedded in the standalone build and available at `web/public/assets/coastal_map_data.json` for static hosting.

## V10 finish pass
The additional folded-leaf trees, tea shrub, distant canopy and service-bay geometry are original procedural Blender work. Cloud atmosphere, material grain, contact particles, turn guidance and boost trails are original code-based effects, not copied racing-game artwork. Workshop credits have no monetary value and remain in local browser storage. No uploaded finish-quality reference images, game logos, purchased audio or commercial game effects are distributed.

## Reconstructed V12 models and showroom
The four additional original arcade vehicle interpretations, coastal loft and model-rendered gallery thumbnails were built anew after the unpublished workspace was lost. They are not recovered copies of the former V12 files. Their private reference photographs are excluded, and no operator/manufacturer logos or downloaded commercial geometry are embedded. Procedural per-car sound profiles are original synthesis, not authentic manufacturer recordings. Exact editable-source, exported-mesh and thumbnail provenance is recorded in `assets/cars/*/manifest.json` and asset QA reports.

No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. The authorized correction to mistaken original-asset CC0 wording is forward-looking only: it does not erase earlier public versions or establish that any earlier dedication was legally reversed.

## V15 aircraft and airtime infrastructure
The two fictional light-twin helicopter variants, articulated rotor/searchlight kit, rotor blur geometry and route-aligned ramp decks are original Blender work. Public primary aircraft images informed broad proportions only; no manufacturer branding, CAD, downloaded mesh or photographic texture is included. Audio is original synthesis. The user's shared race video was analyzed outside the game tree; neither the video nor its frames are distributed. The bounded ramp/airtime reward implementation is original, not a claim to reproduce that video's undisclosed formula. Existing OSM attribution still applies to coastal positioning.

## V17 coastal pavilion UI candidate
`web/src/showroom-scene.js` is original procedural project geometry/material code, with existing original palm models reused without modifying their source assets. `web/src/showroom-reflector.js` is the Reflector helper from the pinned Three.js 0.170.0 package under the existing Three.js MIT license (`web/public/vendor/THREE_LICENSE.txt`); its attribution is preserved. Private uploaded UI references and their local inspection derivatives are not included as textures, source assets, or archive entries.

## Rigged two-officer capture (V17 R3.6)
The anatomical base mesh, morph, skeleton, weights and skin texture are MakeHuman Community / MPFB CC0 asset data, pinned to MPFB v2.0.18 and the publisher's official CC0 system-assets archive. Data Collection AB, Joel Palmius and Jonas Hauquier are credited by the source. Full asset dedication: `web/public/licenses/MAKEHUMAN_CC0.txt`; original licensing distinction, byte hashes and public source URLs: `assets/capture_humans/source/`. No MPFB application code/add-on was installed or executed, and no application-code licence is applied to the CC0 data.

Uniform/driver clothing, capture staging, skeletal posing, materials, door overlays and wrist restraints are original project work. The CPO uniform manual informed original geometry only; its photographs/PDF and private references are excluded. Original additions retain the existing project rights scope. `web/public/vendor/addons/utils/SkeletonUtils.js` is from pinned Three.js 0.170.0 under the existing MIT notice. No paid or extracted commercial-game assets are included.

## NVIDIA SimReady pilot

NVIDIA SimReady assets **barrier_fence_metal_a02** and **crate_blue_a01**, by NVIDIA.
Source: https://huggingface.co/datasets/nvidia/simready-assets/tree/9eadae061bf3f6fcee629b3286d5593c05415b42
Licensed under Creative Commons Attribution 4.0 International: https://creativecommons.org/licenses/by/4.0/ .
Modified: USD to GLB conversion, geometry reduction and texture resizing. No NVIDIA endorsement implied. Full individual licences, package manifests and original dependency hashes are retained under assets/simready/.
