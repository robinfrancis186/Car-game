# V17 R3.7 Maps Git-to-production handoff

The parent task exclusively owns Vercel publication and live verification. This executor does not invoke Vercel. Canonical target: `malabar-hot-coast`, project `prj_wpjGOHOOw8yWEFnoKJeBe8ZTu6d5`, https://malabar-hot-coast.vercel.app/.

From the verified pushed commit run `node tools/build-static.mjs` and publish only `dist/vercel`. `deployment/runtime-manifest.json` maps all 175 public paths to committed source bytes and SHA-256; it also supports connector uploads directly from Git. Do not upload repository/authoring/reference files, `.git`, local review files or private photos.

`runtime_tree_sha256` hashes sorted public-path + NUL + file-SHA256 + newline for the 174 content files excluding `release.json`, avoiding its self-reference. `full_runtime_tree_sha256` hashes all 175 mapped files including `release.json`. Both algorithms are explicit in the manifest; verify every mapped byte as well.

Rollback baseline is the current verified R3.6 deployment from source `b04f65632fba1abdc2aec685126f8e17879bed83`. Parent must retain that deployment before promotion; its deployment ID was not supplied here. Exact R3.6 source release/runtime/validation metadata is preserved in `deployment/history/r3-6/`. Older R3.5 verification remains in `deployment/history/r3-5/`. No deployment has been altered by this executor.

`deployment/maps-source-manifest.json` proves the application/asset bytes match the approved ZIP (SHA256 `f47d2ac1af5e8c39663fa54c7f7e72b256ad54c35411a9fc2bd9fb98e9095297`); release bookkeeping is additional. `publication-checks.json` records 59/59 aggregate stages,22 actual destination launches,stale-selection/save/history/layout checks and builds. The inherited payload-audit CC0 exception is recorded as a failure, not hidden or relabelled. Original assets/licences and unrelated lighting work are unchanged.

Root `production-verification.json` is explicitly pending R3.7 and is not live proof. After deployment the parent must verify exact Git commit, live `release.json`, and all mapped file hashes; then record real deployment/commit IDs and results. No account, project, security setting or credential changes are required.
