"""Authorized forward-only notice correction. Immutable recovery/history is not edited."""
from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
NOTICE='No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.'
replacements={
'The environment asset package separately carries a CC0 dedication.':NOTICE,
'Original environment geometry and generated material definitions are dedicated under CC0 1.0 (`LICENSE.txt`).':'Original environment geometry and generated material definitions were created for this project. '+NOTICE+' See `LICENSE.txt`.',
'Derived exclusively from original CC0 project geometry;':'Derived exclusively from original project geometry. '+NOTICE+' ',
'Original procedural geometry, CC0 dedication;':'Original procedural geometry. '+NOTICE+' ',
'Original procedural geometry, CC0 dedication.':'Original procedural geometry. '+NOTICE,
'Original procedural meshes and per-vertex colors, CC0.':'Original procedural meshes and per-vertex colors. '+NOTICE,
'Original procedural geometry and vertex colors, CC0.':'Original procedural geometry and vertex colors. '+NOTICE,
'Original generated geometry and textures: CC0-1.0 dedication.':'Original generated geometry and textures. '+NOTICE,
'Original procedural geometry authored for this project, dedicated to CC0 1.0 Universal.':'Original procedural geometry authored for this project. '+NOTICE,
'All shipped infrastructure, urban modules, vehicles and houseboat geometry is original procedural Blender work, with CC0 dedication recorded in the respective asset manifests/licenses.':'All shipped infrastructure, urban modules, vehicles and houseboat geometry is original procedural Blender work. '+NOTICE,
'New procedural geometry and scripts are dedicated CC0.':'New procedural geometry and scripts were created for this project. '+NOTICE,
'Original procedural geometry/materials, CC0.':'Original procedural geometry/materials. '+NOTICE,
'CC0-1.0 original geometry/materials; no reference photos or external assets':'Original geometry/materials; no reference photos or external assets. '+NOTICE,
}
report=[]
for base in [ROOT/'assets',ROOT/'blender',ROOT/'web/public',ROOT/'LICENSES.md']:
 for p in ([base] if base.is_file() else sorted(base.rglob('*'))):
  if not p.is_file() or p.suffix.lower() not in {'.py','.json','.md','.txt'}:continue
  raw=p.read_bytes();s=raw.decode();t=s
  if p==ROOT/'assets/environment/LICENSE.txt':
   t='Original project environment material\n\n'+NOTICE+'\n\nAll assets in this package were procedurally modeled for the project; no external mesh or texture is included. OSM-derived placement/data and third-party dependencies retain their separate required notices.\n\nThis forward-looking notice correction does not erase prior published versions or assert that any earlier dedication was legally reversed.\n'
  else:
   for a,b in replacements.items():t=t.replace(a,b)
  if s!=t:
   p.write_text(t);report.append({'path':str(p.relative_to(ROOT)),'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'occurrences_removed':len(re.findall(r'\bCC0\b',s,re.I))-len(re.findall(r'\bCC0\b',t,re.I))})
out={'scope':'Forward-only authorized original-asset notice correction; immutable source/history untouched. No assertion of reversal of prior dedication.','replacement':NOTICE,'preserved':'OSM ODbL and negative no-CC0 notice, Three MIT, font OFL and dependency notices are unchanged.','files':report}
p=ROOT/'tests/recovery/license_correction_manifest.json';p.write_text(json.dumps(out,indent=2)+'\n');print('Corrected',len(report),'files')
