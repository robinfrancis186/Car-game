"""Read-only verification of the frozen runtime, static package and native source hashes."""
from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parents[1]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
release = json.loads((root / 'SOURCE_MANIFEST.json').read_text())
for entry in release['runtime_files']:
    assert sha(root / entry['path']) == entry['sha256'], entry['path']
receipt = json.loads((root / 'deployment/production-verification.json').read_text())
for entry in receipt['files']:
    assert sha(root / 'dist/vercel' / entry['path']) == entry['expected_sha256'], entry['path']
assets = json.loads((root / 'ASSET_SOURCE_MANIFEST.json').read_text())
for entry in assets['files']:
    assert sha(root / entry['path']) == entry['sha256'], entry['path']
print(f"PASS {len(release['runtime_files'])} frozen runtime files, {len(receipt['files'])} exact static production files, {len(assets['files'])} editable Blender scenes")
