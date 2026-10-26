"""Publish metadata-only native copies; leave exact local authoring files intact."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
H=lambda data:hashlib.sha256(data).hexdigest()
paths=[ROOT/'assets/capture_humans/capture_officer_garment_fix.blend',*sorted((ROOT/'assets/capture_humans/exports').glob('*.blend'))]
rows=[]
for source in paths:
 if source.stem.endswith('.public'):continue
 raw=subprocess.check_output(['zstd','-q','-dc',str(source)]);clean=bytearray(raw);ranges=[];start=0
 while True:
  start=raw.find(b'/Users/',start)
  if start<0:break
  end=raw.index(b'\0',start);value=raw[start:end];name=Path(value.decode()).name
  replacement=('//'+name).encode()if'.'in name else b'//'
  assert len(replacement)<=end-start
  clean[start:end]=replacement+b'\0'*(end-start-len(replacement));ranges.append((start,end));start=end
 assert len(clean)==len(raw)
 assert all(any(lo<=i<hi for lo,hi in ranges)for i,(a,b)in enumerate(zip(raw,clean))if a!=b)
 assert not any(marker in clean for marker in [b'/Users/',b'/tmp/',b'user_reference',b'library_file_id',b'libfile_'])
 target=source.with_name(source.stem+'.public.blend');packed=subprocess.check_output(['zstd','-q','-3','-c'],input=clean);target.write_bytes(packed)
 rows.append({'path':str(target.relative_to(ROOT)),'bytes':len(packed),'sha256':H(packed),'original_authoring_sha256':H(source.read_bytes()),'changed_fields':len(ranges),'changes':'NUL-terminated absolute metadata paths only; all other decompressed bytes identical','private_markers_remaining':0})
(ROOT/'deployment/capture-native-source-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Created',len(rows),'metadata-only public native copies; originals preserved.')
