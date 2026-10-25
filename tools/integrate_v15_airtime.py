"""Idempotently attach original V15 assets/config without changing base geometry."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'web/public/assets';W=R/'assets/web'
ramps=json.loads((R/'assets/airtime/ramp_manifest.json').read_text())
for name,ramp in zip(['course_runtime.json','course_runtime_highlands.json'],ramps):
 p=P/name;data=json.loads(p.read_text());cfg={k:ramp[k]for k in ['id','startS','lipS','rise','centerOffset','halfWidth']};cfg['minSpeed']=12
 for block in [data,data.setdefault('world',{})]:
  block['ramps']=[cfg];block['air_traffic']=True
  meshes=block.get('course_meshes')
  if meshes is not None:
   meshes[:]=[m for m in meshes if m.get('file')not in['Coast_AirtimeRamp.glb','Highland_AirtimeRamp.glb']]
   meshes.append({'file':ramp['asset'],'collision':'model-ramp-surface','provenance':'Original V15 authored ramp. Existing route and attribution preserved.'})
 b=(json.dumps(data,indent=2)+'\n').encode();p.write_bytes(b);(W/name).write_bytes(b)
 if name.endswith('highlands.json'):(R/'assets/highlands'/name).write_bytes(b)
print('V15 ramp/air-traffic world metadata attached; existing route coordinates unchanged.')
