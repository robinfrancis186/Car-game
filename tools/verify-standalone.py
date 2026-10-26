"""Verify embedded source/assets in an already-built standalone; not browser/GPU QA."""
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html_path = root / "dist/malabar-hot-coast.html"
raw = html_path.read_bytes()
html = raw.decode("utf-8")
match = re.search(r'<script>window\.__MALABAR_ASSETS__=(\{.*?\});</script>', html)
assert match, "Embedded asset map missing"
assets = json.loads(match.group(1))
source_dir = root / "web/public/assets"
expected = {
    p.name for p in source_dir.iterdir()
    if p.suffix in {".glb", ".json"} or re.fullmatch(r"car_thumb_[a-z]+\.png", p.name)
}
expected.update("map-previews/" + p.name for p in (source_dir / "map-previews").glob("*.png"))
assert set(assets) == expected, "Embedded inventory differs from build source"
for name, uri in assets.items():
    prefix, encoded = uri.split(",", 1)
    assert prefix.endswith(";base64"), name
    assert base64.b64decode(encoded, validate=True) == (source_dir / name).read_bytes(), name
previews = sorted((source_dir / "map-previews").glob("*.png"))
assert len(previews) == 11, "Expected all canonical destination previews"
for preview in previews:
    uri = "data:image/png;base64," + base64.b64encode(preview.read_bytes()).decode()
    assert assets.get('map-previews/' + preview.name) == uri, "Destination preview not embedded exactly: " + preview.name
# Runtime prefers these embedded keys; raw source retains its split-runtime fallback.
font = base64.b64encode((source_dir / "fonts/display.ttf").read_bytes()).decode()
assert "data:font/ttf;base64," + font in html
assert '<script type="importmap">' not in html
assert 'src="./src/main.js"' not in html
assert 'href="./src/style.css"' not in html
bundle = (root / "dist/game.bundle.js").read_text()
escaped_bundle = re.sub(r"</script", r"<\\/script", bundle, flags=re.I)
assert "<script>" + escaped_bundle + "</script>" in html
for license_path in [source_dir / "fonts/OFL.txt", root / "web/public/vendor/THREE_LICENSE.txt"]:
    assert license_path.read_text().replace("-->", "-- >") in html
result = {
    "result": "PASS", "scope": "Built bytes and embedded inventory; no rendering or GPU assertion",
    "standalone_bytes": len(raw), "standalone_sha256": hashlib.sha256(raw).hexdigest(),
    "embedded_assets_byte_identical": len(assets), "map_previews_embedded_exact": len(previews), "font_embedded_exact": True,
    "bundle_embedded_exact": True, "third_party_notices_preserved": True,
}
output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / "tests/v17/r3-2-evidence/standalone-integrity.json"
output.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
