"""Capture the bounded V14.1 source/CSS patch after exact-preview acceptance."""
from pathlib import Path
import hashlib, json, datetime, subprocess, sys

R = Path(__file__).resolve().parents[1]
H = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable, str(R/'tools/check_v14_1_patch.py')], check=True)
paths = [R/'web/index.html'] + [p for folder in ['web/src', 'web/public'] for p in (R/folder).rglob('*') if p.is_file()]
rows = [{'path': p.relative_to(R).as_posix(), 'bytes': p.stat().st_size, 'sha256': H(p)} for p in sorted(paths)]
tree = hashlib.sha256(''.join(x['path']+'\0'+x['sha256']+'\n' for x in sorted(rows,key=lambda x:x['path'])).encode()).hexdigest()
names = [
 'dist/malabar-hot-coast.html', 'dist/game.bundle.js', 'dist/v14-1-ui-preview.html', 'dist/v14-1-ui-frame.html',
 'web/package.json', 'web/package-lock.json', 'web/build-standalone.mjs', 'web/build-ui-preview.mjs',
 'tests/v14_1/full_gate.log', 'tests/v14_1/final_gate_receipt.json',
 'tests/ui_audit_v14_1/BASELINE.json', 'tests/ui_audit_v14_1/NATIVE_FINDINGS.md',
 'tests/ui_audit_v14_1/patch_scope.json', 'tests/ui_audit_v14_1/play_hero_projection.json',
 'tests/ui_audit_v14_1/ACCEPTANCE.md', 'tests/ui_audit_v14_1/LEAD_VISUAL_REVIEW.md',
 'tests/recovery/standalone_integrity.json',
]
report = {
 'candidate': 'MALABAR V14.1 bounded UI acceptance patch',
 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'base': 'Verified live V14 Sites 28 commit 5c34079477607a363575d21fbb26d37d8ff34803',
 'status': 'Source/model/controller and exact CSS-preview gates passed; native patched WebGL/touch acceptance remains separate.',
 'intended_runtime_changes': ['web/src/main.js', 'web/src/style.css'],
 'scope': ['Tall compact portrait Play picker/Garage flow clears measured hero band without changing camera', 'Short-landscape route text contrast and legibility', 'Insufficient-upgrade copy explicitly says more coins'],
 'protected': 'All other 115 runtime files exact; controller normalized to baseline by replacing only shortage text. No assets, renderer, physics, storage, currency or economy changes.',
 'runtime_tree_sha256': tree,
 'tree_algorithm': 'SHA256 of sorted relative-path + NUL + file SHA256 + newline',
 'runtime_files': rows,
 'anchors': {n: {'bytes': (R/n).stat().st_size, 'sha256': H(R/n)} for n in names},
 'limits': ['Preview screenshots are renderer-stub/scene-graph projection evidence, not new gameplay GPU captures', 'Actual V14 native findings are parent-reported with screenshots retained on Mac; no claim this builder viewed those pixels', 'No new human driving, native touch or auditory acceptance claim'],
 'license': 'Required OSM, Three.js and font notices and approved neutral original-material wording preserved; no history rewrite or revocation claim.',
}
(R/'tests/release/V14_1_RELEASE.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'runtime_tree_sha256': tree, 'runtime_files': len(rows), 'standalone': report['anchors']['dist/malabar-hot-coast.html']}, indent=2))
