# V17 R3.9 scoped first-polish candidate

Parent owns Git publication, Vercel and live verification. No push/deploy here. Preserve live R3.8 source 5867a858f98fd4b02d051bb1f23abbab1eaeb75f and its deployment for rollback. Prior metadata is retained under deployment/history/r3-8/.

Build split runtime: `node tools/build-static.mjs`, output `dist/vercel`. Exact public-byte mapping/hashes are in deployment/runtime-manifest.json. Standalone: `npm --prefix web run build`; verifier: `python3 tools/verify-standalone.py` (create its legacy report directory tests/v17/r3-2-evidence first). Public licence/attribution files are unchanged and included.

63/63 aggregate stages passed. Later changes only clarify/disable wall assist in UI and correct a module comment; affected controller, surface, Maps, Home and actual browser checks passed afterward. All 11 map destinations remain, with 20 normal Auto starts tested across two viewports. 30 full route/rate model probes passed. Native audio sampled signals passed; listening is not validated. Exact receipts are under r3-9/validation/.

The original 138-file protected baseline remains intact. Only web/src/audio.js has an explicit approved exception: old/current hashes and behavioral suites are checked via web/tests/polish-audio-scope.json/mjs. Other 137 files remain byte-identical. No other protected path is exempted.

Auto follows the existing road, offers left/center/right lines and a visible brake override, while Manual remains available without changing physical race progress. Pedals-only is a separate Help option. Harbour Wall Run staysManual: its 3D banked adhesion and minimum attachment speed need a dedicated surface-frame controller. The limitation is explicit in Maps/Help and its assist selector is disabled.

No new art/dependencies or third-party media were added. Asphalt is concept reference only; original game art/branding remains. The existing payload audit still rejects unchanged CC0 character grant metadata; independent byte/dependency/licence checks apply, with grants preserved.

No physical-phone/Safari/human listening/new-player validation, no guaranteed collision avoidance, race wins or police evasion, and no 9/10 rating claim. This first candidate does not complete the ten-area plan.
