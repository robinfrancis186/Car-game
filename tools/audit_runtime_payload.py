"""Read-only release payload audit. Original authoring metadata is not a license grant."""
from pathlib import Path
import hashlib,json,re,struct,io,base64
R=Path(__file__).resolve().parents[1];A=R/'web/public/assets';rows=[]
for p in sorted(A.iterdir()):
 if not p.is_file():continue
 b=p.read_bytes();row={'name':p.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 assert p.suffix in {'.glb','.json','.png'},f'Unexpected runtime asset {p}'
 if p.suffix=='.glb':
  assert b[:4]==b'glTF';n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);row['external_uris']=[v['uri']for k in('images','buffers')for v in g.get(k,[])if v.get('uri')and not v['uri'].startswith('data:')];assert not row['external_uris'],p.name+' external dependency'
  hits=re.findall(r'.{0,50}(?:CC0|public.domain dedication).{0,70}',json.dumps(g),re.I);assert not hits,p.name+' original grant metadata';row['grant_metadata_matches']=0
  row['embedded_images']=[]
  for image in g.get('images',[]):
   if 'bufferView' in image:
    view=g['bufferViews'][image['bufferView']];assert view.get('buffer',0)==0;start=20+n+8+view.get('byteOffset',0);raw=b[start:start+view['byteLength']]
   elif image.get('uri','').startswith('data:'):raw=base64.b64decode(image['uri'].split(',',1)[1])
   else:raise AssertionError('Unresolved embedded image')
   from PIL import Image
   im=Image.open(io.BytesIO(raw));im.load();row['embedded_images'].append({'name':image.get('name'),'sha256':hashlib.sha256(raw).hexdigest(),'dimensions':list(im.size),'mode':im.mode})

 if p.suffix=='.png':
  from PIL import Image
  im=Image.open(p);im.load();row['dimensions']=list(im.size);row['mode']=im.mode
  if p.name.startswith('car_thumb_'):assert im.size==(512,320)and im.mode=='RGBA'
 rows.append(row)
report={'scope':'Actual runtime bytes, external-dependency/hidden-grant checks and decoded PNG headers/pixels; not visual/GPU acceptance.','files':rows}
out=R/'tests/recovery/runtime_payload_audit.json';out.write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(rows),'runtime assets; no external GLB resources or original-asset grant metadata; PNG decoding passed.')
