# ServiceShowroomLoft — V13 bounded coastal realism pass

Original project geometry and original mathematical microstructure maps; reuse license not selected by owner. No reference photo pixels, downloaded models or manufacturer branding are shipped. The user screenshot informed criticism/composition only.

## Changes from V12
- Four individually curved, tapered, growth-ringed palms; 68 three-dimensional arched fronds, 3,264 individually editable folded narrow leaflets, small crown/coconut attachments. Upper, middle and drooping tiers vary per tree; no umbrella disks or opaque balloon crowns.
- Low undulating bank, thin uneven shore and two restrained distant low headlands replace the perfectly straight lawn/ocean join. These are contained showroom scenery, not an expanded race map.
- Rounded tapered ceramic planters with recessed soil and folded lance leaves replace box planters.
- Basalt floor keeps exactly the same mesh/stage plane. Original periodic 128px micro-normal and roughness images are packed in native source and embedded in the GLB. UV repeat period is 0.38m. The GLB roughness factor is1, G texture range80–95/255; metallic factor0.07 with B texture1. No displacement.

## Assets and budget
- `ServiceShowroomLoft.blend`: 3,810 named editable mesh objects, no car.
- `assets/web/ServiceShowroomLoft.glb` and identical public copy: 33,802 triangles, 13 draws, 2,571,276 bytes. V12 baseline:23,222 triangles/11 draws/1,322,220 bytes.
- Main generator: `blender/build_showroom_loft.py`.
- Existing architecture/stage scale remains20×16m with roof6.25–6.65m. Open front +Z in glTF; live car +X. Floor slabY0, tiny unchanged joint inlays up to1.2mm.
- Material names and lights remain in `loft_manifest.json`. New distant layers add only `Loft_Coastal_Bank` and `Loft_Distant_Headland`. Microstructure adds no draws.

## Verification
- `loft_validation.json`: actual Three GLTFLoader, 81 clear car-camera rays, 9 stage rays, finite geometry, zero degenerate triangles and identical staged/public copies. Node PNG shim validates image headers/wiring, not GPU rendering.
- `loft_native_validation.json`: editable source, four trunks,68 fronds,3,264 folded leaflets; no baked car; two original packed maps; metre-UV agreement.
- `loft_v13_binary_validation.json`: all exported normals unit within1.4e-7; original PNGs fully decoded using Pillow. Exact triangle positions of floor, steel structure, timber, glazing, light strips and brass are identical to V12 (ignoring UV-driven vertex splits). Floor roughness/metalness multiplication verified from actual GLB.
- Matched before/after Blender renders are actual GLB reimports using identical camera/lights and the same separately loaded red car. They are CPU Cycles composition previews, **not gameplay/WebGL screenshots**.64 samples; no denoising backend available.
- Generator removes72 existing zero-area bevel faces after float32 export, without moving vertices. No route, terrain, physics or collider files edited.

## Limits
This is a bounded believable-material/foliage increment, not a photoreal/AAA claim. The palms remain mobile-budget geometry; distant headlands are low scenic silhouettes. Lighting/reflections in the browser depend on the runtime renderer. Native preview and GLB share the floor image maps rather than using unsupported prettier procedural-only materials.

Final V13 images use explicit filenames `ServiceShowroomLoft_V13_before.png` and `ServiceShowroomLoft_V13_after.png`. Older unversioned/home composition images retained in this directory are V12 reference evidence, not new V13 renders.
