"""Verify generated standalone bytes against the actual split payload and notices."""
from pathlib import Path
import json,hashlib,base64,re
R=Path(__file__).resolve().parents[1];html=(R/'dist/malabar-hot-coast.html').read_text()
m=re.search(r'window\.__MALABAR_ASSETS__=(\{.*?\});</script>',html);assert m,'Missing embedded asset table'
assets=json.loads(m[1]);rows=[]
for name,url in sorted(assets.items()):
 b=base64.b64decode(url.split(',',1)[1]);p=R/'web/public/assets'/name;assert b==p.read_bytes(),name
 rows.append({'file':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
expected={p.name for p in(R/'web/public/assets').iterdir()if p.suffix in('.glb','.json')or re.fullmatch(r'car_thumb_[a-z]+\.png',p.name)}
expected.update("map-previews/"+p.name for p in(R/'web/public/assets/map-previews').glob("*.png"))
assert set(assets)==expected
for notice in ['web/public/vendor/THREE_LICENSE.txt','web/public/assets/fonts/OFL.txt']:
 assert(R/notice).read_text().replace('-->','-- >')in html,notice
assert 'src="./src/main.js"'not in html
assert 'OpenStreetMap'in html and 'ODbL'in html and 'https://www.openstreetmap.org/copyright'in html
out={'result':'PASS','embedded_assets':len(rows),'standalone_sha256':hashlib.sha256((R/'dist/malabar-hot-coast.html').read_bytes()).hexdigest(),'files':rows,'notices':'Three.js and font full notices present; linked OSM/ODbL attribution retained.','limits':'Byte identity and notices only; not a browser execution or rendering check.'}
(R/'tests/recovery/standalone_integrity.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='files'},indent=2))
