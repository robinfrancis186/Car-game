# NVIDIA SimReady visual pilot

Assets: barrier_fence_metal_a02 and crate_blue_a01, by NVIDIA.
Source: https://huggingface.co/datasets/nvidia/simready-assets/tree/9eadae061bf3f6fcee629b3286d5593c05415b42
Licence: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Individual package manifests and full licences are retained beside this file.
Modified: USD to GLB conversion, geometry reduction and texture resizing using Blender 5.2.1. No NVIDIA endorsement implied.

Pinned dependency receipt lists all original hashes; the exact minimal USD source and texture dependencies are retained under source/. Rebuild with the existing Blender: blender --background --python assets/simready/optimize-simready.py. Runtime GLBs are in web/public/assets. The authored USD mesh/material transforms are retained, including crate UV mapping. Visual-only placements do not alter collision or gameplay. Desktop uses near/far LODs; mobile-sized balanced mode uses far meshes and existing shadows-off policy.
