"""Verify complete private source backup against release and archive manifests."""
from pathlib import Path
import json,zipfile,hashlib,sys
R=Path(__file__).resolve().parents[1];P=Path(sys.argv[1]);H=lambda b:hashlib.sha256(b).hexdigest();release=json.loads((R/'tests/release/V16_1_RELEASE.json').read_text())
with zipfile.ZipFile(P)as z:
 assert z.testzip()is None; names=set(z.namelist());manifest=json.loads(z.read('FULL_BACKUP_MANIFEST.json'))
 for row in manifest['files']:assert H(z.read(row['path']))==row['sha256'],row['path']
 for row in release['runtime_files']:assert H(z.read(row['path']))==row['sha256'],row['path']
 assert not any(n.startswith('references/')and not n.startswith('references/route/')for n in names)
 assert not any('/node_modules/'in n or'/.git/'in n or n.startswith('.git/')for n in names)
 native=[n for n in names if n.endswith('.blend')]
result={'path':str(P),'bytes':P.stat().st_size,'sha256':H(P.read_bytes()),'archive_files':len(names),'runtime_files':len(release['runtime_files']),'native_blender_sources':len(native),'all_manifest_bytes_exact':True,'crc':'PASS','private_reference_inputs_excluded':True,'scope':'Complete reproducible source/build evidence; CSS/native acceptance remains separately gated.'}
(R/'tests/v16_1/FULL_CHECKPOINT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');P.with_suffix('.verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
