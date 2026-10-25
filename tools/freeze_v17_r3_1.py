"""Freeze source-tested unpublished R3.1 only; rendered acceptance remains pending."""
from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parents[1];H=lambda b:hashlib.sha256(b).hexdigest()
p=json.loads((R/'tests/v17/R3_1_PATCH_MANIFEST.json').read_text());a=json.loads((R/'tests/v17/r3-1/aggregate-result.json').read_text())
assert a.get('status')=='PASS' and a.get('npm_test_exit')==0 and a.get('runtime_test_inputs_unchanged') is True,'Aggregate not terminal PASS'
for row in p['runtime_files']:assert H((R/row['path']).read_bytes())==row['sha256'],'Runtime changed: '+row['path']
assert len(p['runtime_delta'])==1 and p['runtime_delta'][0]['path']=='web/src/style.css'
rels=['dist/malabar-hot-coast.html','dist/game.bundle.js','web/package.json','web/package-lock.json','web/build-standalone.mjs','web/tests/v17-r3-1-hit-targets.test.mjs','tests/v17/R3_1_PATCH_MANIFEST.json','README.md','STATUS.md','design-qa.md','docs/v17/R3_1_ACCEPTANCE.md','docs/v17/R3_RENDERED_VISUAL_REVIEW.md','tools/full_checkpoint_v17_r3_1.py','tools/freeze_v17_r3_1.py']
for d in ['tests/v17/r3-1','tools/ui-review-r3-1']:
 rels += [x.relative_to(R).as_posix() for x in (R/d).rglob('*') if x.is_file() and x.name!='FINAL_RELEASE.json' and x.name!='freeze.log']
anchors={x:{'bytes':(R/x).stat().st_size,'sha256':H((R/x).read_bytes())} for x in sorted(set(rels))}
m={'candidate':'MALABAR V17 R3.1 target-size patch','status':'UNPUBLISHED — source tests passed; actual R3.1 pixels/header target bounds, WebGL/native and exact-reference acceptance pending','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_runtime_tree_sha256':p['base_runtime_tree_sha256'],'runtime_tree_sha256':p['runtime_tree_sha256'],'runtime_files':p['runtime_files'],'runtime_delta':p['runtime_delta'],'unchanged_r3_runtime_files':144,'anchors':anchors,'baseline_provenance':'tests/v17/CANDIDATE_MANIFEST.json is inherited frozen R3, not current patch; baseline docs retained under docs/provenance/r3-baseline. Current authoritative manifest is this file.','scope':'Only CSS hit-target sizes and necessary short-landscape header clearances. No economy, saves, physics, controls, assets or scene changes.','visual_evidence':'R3 screenshots in tests/v17/r3-browser-evidence are baseline findings, not proof of R3.1. Actual WebGL cloud root blocked because GL_VENDOR/GL_RENDERER Disabled. Original scene proof remains partial.','private_references_included':False,'publication_authorized':False}
(R/'tests/v17/r3-1/FINAL_RELEASE.json').write_text(json.dumps(m,indent=2)+'\n')
(R/'FULL_BACKUP_MANIFEST.json').write_text(json.dumps({'kind':'Current source-root pointer; archive has its own full-file manifest','candidate':m['candidate'],'current_release_manifest':'tests/v17/r3-1/FINAL_RELEASE.json','runtime_tree_sha256':m['runtime_tree_sha256'],'baseline_manifest':'tests/v17/CANDIDATE_MANIFEST.json','status':m['status']},indent=2)+'\n')
print(json.dumps({k:m[k]for k in ['candidate','status','runtime_tree_sha256','unchanged_r3_runtime_files']}));print('Anchors',len(anchors),'runtime files',len(m['runtime_files']))
