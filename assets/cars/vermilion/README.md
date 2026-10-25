# Vermilion Butterfly GT — fresh reconstruction

This is newly reconstructed original geometry after the unpublished V12 source/control loss. It is **not the old artifact or old hash**, and is not licensed manufacturer CAD or an exact branded replica. Recovered user photographs and earlier previews informed proportions only; no logos, photographic textures or reference pixels are embedded.

**No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.**

Pointed bifurcated front radiators, actual recessed bonnet vents, swept blade lamps, separate red doors, inset circular rear lamps, dark lined intakes and diffuser, fixed wing. Door hinges support static display posing; the intermediate opening path has body contacts. Keep gameplay doors closed. A separately tested1.10rad pose with100mm outward offset is clear, but is not a continuous engineered mechanism.

## Source and deliverables

- `vermilion.blend`: native original editable components, named rigid assemblies.
- `../../../blender/build_vermilion.py`: isolated reconstructed generator.
- `../../../blender/rebuild_car_helpers.py`: original procedural primitives, wheel parts and rigid GLB serializer; shared read-only.
- `../../web/car_vermilion.glb`: optimized actual runtime geometry; public copy byte-identical.
- `vermilion_runtime_roundtrip.blend`: actual GLB reimport before studio dressing.
- `preview_front.png` / `preview_rear.png`: actual-GLB CPU Cycles studio previews, **not gameplay**.
- `../../gallery_thumbnails/car_thumb_vermilion.png`:512×320 transparent actual-model gallery image.

## Shared rig contract

Blender metres: +X forward,+Y left,+Z up. GLB/Three metres: +X forward,+Y up,−Z left. `CAR_ROOT` contains `CarBody` and four `Steer_*` nodes; each steer has `Spin_* > Wheel_*` and separate fixed `Caliper_*`. Axles X±1.35m; hub Y.368m in Three, lateral Z±.924m; nominal tire radius.366m. Actual lowest tire/groove vertex is approximately.001897m above root ground. Front steering local+Y, forward wheel spin local−Z. Validated maximum steering±.45rad with body-only roll±.008,pitch±.005,heave±.002m. Wheels stay independently grounded.

Paint API name is exactly `Crimson multi-coat | original fan concept`, with model-specific authored color. Rear boost sockets are Three[-2.4,.255,−.56] and[-2.4,.255,+.56]. `RearWing` is fixed, not `AeroWing_Hinge`. Performance/flight behavior is fictional arcade tuning supplied by the parent runtime, not production specifications. Actual full bounds and material counts are in the manifest.

## Evidence and scope

- `manifest.json`: fresh reconstruction SHA, dimensions, material/node API, tested limits.
- `pose_validation.json`:756 sampled body/tire checks.
- `brake_validation.json`:364 full-spin fixed-caliper versus alloy spokes/barrel/hub AND actual slotted rotor checks.
- `source_validation.json`: editable native parts, independent spin movement, fixed-caliper matrices and no image dependencies.
- `wing_validation.json`: fixed blade/endplates versus source body; deliberate supports excluded.
- `three_validation.json`: actual Three.GLTFLoader, hierarchies, bounds, every triangle nondegenerate, every normal finite/unit.
- `render_provenance.json`: actual final GLB hash and studio-image hashes, not a high-poly stand-in.

These are sampled mesh/source checks, not continuous collision proof, engineered vehicle validation or browser gameplay certification. Cockpit-camera usefulness, controller integration and actual rendered performance require parent runtime QA.

## Reproduce (from rebuild root)

```sh
blender -b --threads 4 --python blender/build_vermilion.py
CAR_ID=vermilion blender -b --threads 3 --python blender/test_rebuilt_car.py
node blender/validate_rebuilt_car.mjs vermilion
CAR_ID=vermilion CAR_RENDER_MODES=front,rear,thumb CAR_SAMPLES=64 blender -b --threads 4 --python blender/render_rebuilt_car.py
# Inspect both final images and thumbnail before freezing:
python blender/finalize_rebuilt_car.py vermilion
```

Vermilion optional pose audit: `DOOR_PRETRAVEL=.10 blender -b --python assets/cars/vermilion/test_doors.py`. Its retained FAIL for the whole opening path is an explicit limitation, not an ignored runtime wheel/body failure.
