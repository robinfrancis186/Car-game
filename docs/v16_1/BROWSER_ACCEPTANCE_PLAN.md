# V16.1 controlled render check

## Evidence and limits
V16 native Chrome traversed the wall route successfully, but sequential active captures showed roughly 17–21 FPS at 1440×722 and 57–59 FPS at 390×844. Per-sample DPR/backing-buffer size, settling and capture overhead were not controlled. These are point observations, not a benchmark or established cause.

V16.1 leaves Auto resolution exactly unchanged. The only default render optimization places the opaque, depth-tested, non-depth-writing cloud sky after ordinary opaque depth. Transparent effects remain later. No shaders, textures, geometry, lights, contact physics, rewards or saved settings are reduced or retuned. Whether it improves native GPU time is unverified until this comparison.

## Small authorized native window (parent owns controls)
1. Preserve the current car, wallet, upgrades and quality. Do not purchase/reset/alter saved progress. Enter the optional Harbour Wall Run normally. Use the same camera and recorded route position where practical.
2. In Help, show Performance and note CSS size, device DPR, actual BUFFER size, renderer SCALE, MSAA and shadow map. Enable the optional driving pin. Resolution comparisons last only in this page; no save writes.
3. At native desktop viewport, choose **High + Auto**. Resume and allow at least five active seconds without accessibility queries or screenshots. Capture one settled `FPS / 5 S`, P95 and draw-count sample plus route position/bank. This is descriptive RAF timing, not GPU timing.
4. Compare **High + Standard (1×)** at the same camera/route segment, again allowing a full settling window. This changes render pixels only, not car detail or shadows. Reset/restart the solo route normally if needed; no debug teleport.
5. If time allows, compare **Lite + Full (up to 1.6×)** to separate quality/shadows from resolution, and Auto portrait with exact per-sample buffer dimensions. Record any controls/capture overhead. Do not infer a causal result from different route poses alone.
6. Check sky/road/car silhouettes, glass/transparent effects, horizon, and surface HUD text against bright sky. Check surface route/status at 390×844 and short landscape. Cloud CSS screenshots do not establish WebGL visual correctness.
7. Restore **High + Auto**, original viewport, car/save and pause. Report point samples, not sustained FPS guarantees.

Each viewport, camera, quality, resolution, pause/menu or hidden-page change resets the active window. Help pauses and clears it; read buffer settings there, then resume for settled driving-pin timing. The pin remains off by default.

## Reward observation
The observed 1.55 s airtime / 0.04% refill is compatible with near-full battery: adding 0.0004 energy to 0.9996 reaches 1.0. Production `<1% BOOST ADDED` is truthful. Full battery gives `BOOST FULL`; no reward mechanics are changed.
