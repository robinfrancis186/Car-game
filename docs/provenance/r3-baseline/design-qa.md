# V17 R3 design QA

**Final verdict: blocked (work in progress).** This file is not publication authorization.

## Target and scope
User-provided Home, Workshop, Shop and Run Ended references were inspected at actual pixel level, alongside the rejected iPhone V16.1 screenshot. Those private images are inspection inputs only and are excluded from the runtime and full-source backup.

R3 is isolated from V16.1, R1 and R2. Its intended delta is compact nonduplicated Home navigation, consistent responsive hierarchy, and original 3D coastal-showroom lighting/material/environment improvement. Physics, economy, coins, storage, audio, controls, routes and multiplayer are not redesign targets.

## Gates
- Actual R3 DOM/CSS screenshots at 1440×722, 390×844, 844×390 and 320×568: blocked: supported cloud browser cannot reach executor loopback; no documented preview forwarding is available.
- Same-viewport reference/implementation visual comparison: blocked pending R3 screenshot evidence.
- Actual R3 WebGL scene rendering: blocked in current cloud browser (GL_VENDOR/GL_RENDERER Disabled, BindToCurrentSequence failed in prior read-only live tests).
- Original Blender proof: generated and actually inspected at 960×519, 384 CPU samples. See below. It cannot establish WebGL integration or game FPS.
- Native-device scene/performance acceptance: pending.
- No publication authorized; Sites37 R2 denial remains respected.

## Known gaps
P0: No exact-match or final acceptance claim without actual rendered R3 evidence.
P1: Original car models are stylized compared with the references; Shop transparent thumbnails still lack equivalent photographic coastal scenes.
P1: New live 3D lighting/reflection/camera must be reviewed in a WebGL-capable browser before publishing.
P2: Mobile is a responsive adaptation of landscape reference layouts, not a literal scaled screenshot.

## Local preview attempt (18:57 UTC)
The normal HTTP server was bound only to `127.0.0.1:8088` and served a directory containing only the synthetic, save-isolated UI preview. Existing supported cloud CUA navigation returned `net::ERR_CONNECTION_REFUSED`. A subsequent attempt to read that failed tab was rejected by the browser URL policy (requested protocol not allowed; only HTTP/HTTPS allowed). Inspection stopped immediately and the local server was stopped. No alternate host/protocol, firewall change, publication, custom Chromium process or launch flags were attempted. This is an unavailable local-preview connection plus an explicit failed-tab observation denial, not a rendered application defect. Exact record: `tests/v17/r3-local-preview-blocker.json`.

## Corrected original scene proof (19:05 UTC)
Actual pixels inspected: `tools/scene-proof-r3/proof-final-corrected/pavilion-crimson.png`, SHA-256 `df9eb7e1a7bb39a2ce0507b91a92c32da18599d0d38065b848bd33d8f0ef93d7`. It uses the unchanged original Crimson model and exported runtime pavilion geometry; no private reference pixels or UI overlay. The source receipt lists exact meshes, camera, input hashes and Blender approximations.

Visible improvements compared with the rejected pale V16.1 screenshot: darker steel/cedar enclosure, stronger warm car highlights, slate-floor reflections and a larger focal car. Actual visual inspection caught an orange finite-sea-edge wedge and a dark headland bar; the corrected proof no longer shows either. A proposed garage zoom was rejected because real model-bound tests caught clipping; the closer fit is Home-only and retains garage/portrait limits.

**Still not an exact reference match:** gray/flat sea, simplified repetitive foliage, stylized original car, less cloud/sky and coastal detail, and a more-cropped ceiling remain visible gaps. Shop cards remain original transparent car thumbnails without reference-equivalent scenic photography. The offline proof uses Blender equivalents for the Three.js sky/ocean/reflection shaders and lighting; it is neither actual WebGL output nor UI screenshot evidence. No further art batch is included in this checkpoint.

## Final source aggregate
`npm test` completed successfully with final runtime inputs unchanged throughout the run. The aggregate includes inherited gameplay/controller/storage/simulation tests, seven-car scene/projection checks, new Home navigation tests, byte preservation and 48 menu-mode lighting/environment/exposure transitions. All 138 protected V16 files and 139/143 original V16.1 runtime files are exact. Standalone build: 72,223,269 bytes, 106 embedded assets; standalone SHA-256 `3c1c1075c7dc7d036723d4c7424d0c91bd0e30f13ef33bb8a54096631d420b20`. Asset/notice/external-resource audits and CSS parse pass. None of these tests resolve the actual R3 CSS/WebGL/native-device gates above.
