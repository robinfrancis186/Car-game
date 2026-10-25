# Bronze Apex — reconstructed original arcade coupe

Built anew in Blender on 2026-10-23 from private silhouette references. This is an original stylized interpretation, not an exact recovery of the lost former V12 asset, a licensed replica, or a manufacturer simulation. No reference image, trademark texture or third-party mesh is embedded.

- Editable source: `bronze_apex.blend`; generator: `blender/build_bronze.py`.
- Game asset: `assets/web/car_bronze.glb`, byte-identical public copy.
- Native +X forward / +Z up; exported +X forward / +Y up.
- Four independent steering/spin pivots and fixed brake calipers; front steering limit 0.45 rad; nominal rolling radius 0.366 m.
- Hood and door panels are separate rigid nodes but remain closed in this release. A mechanical opening sequence is not provided or claimed.
- RearWing is fixed under the visual chassis, not the Silver Roadster active-wing hinge.
- Actual exported geometry passed 756 sampled body/tire poses, 364 brake rotations, native wheel independence and fixed-wing checks, plus indexed triangle/normal/axis/size checks. These are sampled asset contracts, not full physical engineering certification.
- Front/rear/thumbnail images were rendered from the actual exported GLB with original studio lighting; they are not gameplay screenshots. No denoising backend is available in this Blender build.
- Runtime paint, camera, coin ownership and driving acceptance are tested separately by the game integration suites.

No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. This forward-looking statement does not rewrite earlier public versions or establish that any earlier dedication was legally reversed.
