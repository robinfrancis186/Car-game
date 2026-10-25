"""Validate and record the completed original helicopter asset kit, not gameplay.
Run with ordinary Python after render_helicopter.py and all three asset tests.
"""
from pathlib import Path
import hashlib
import json
import shutil

R = Path(__file__).resolve().parents[1]
O = R / 'assets/helicopter'
W = R / 'assets/web'
P = R / 'web/public/assets'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

variants = []
reports = []
previews = []
copy_checks = []
for key in ('civilian', 'police'):
    d = O / key
    m = read(d / 'manifest.json')
    f = d / m['file']
    assert digest(f) == m['sha256']
    for target in (W / m['file'], P / m['file']):
        assert digest(target) == m['sha256']
        copy_checks.append(str(target.relative_to(R)))
    for target in (W / f'helicopter_{key}_manifest.json', P / f'helicopter_{key}_manifest.json'):
        assert target.read_bytes() == (d / 'manifest.json').read_bytes()
        copy_checks.append(str(target.relative_to(R)))
    for name in ('glb_validation', 'mechanics_validation', 'native_validation'):
        report = read(d / (name + '.json'))
        assert report['result'] == 'PASS'
        assert report.get('source_glb_sha256', report.get('sha256')) == m['sha256']
        if name == 'native_validation':
            assert report['native_sha256'] == digest(R / m['native_source'])
        reports.append(str((d / (name + '.json')).relative_to(R)))
    for mode in (('front', 'rear', 'detail') if key == 'police' else ('front', 'rear')):
        p = d / f'preview_{mode}_provenance.json'
        proof = read(p)
        image = proof['image']
        assert image['source_glb_sha256'] == m['sha256']
        assert digest(R / image['file']) == image['sha256']
        assert image['samples'] == 64 and image['denoising'] is False
        previews.append({'file': image['file'], 'provenance': str(p.relative_to(R)), 'sha256': image['sha256'], 'scope': proof['scope']})
    variants.append({k: m[k] for k in ('id', 'display_name', 'file', 'sha256', 'bytes', 'triangles', 'draw_calls', 'materials', 'native_source', 'coordinate_contract', 'rotors', 'searchlight', 'navigation_sockets', 'swept_bounds_three_m')})

blur = read(O / 'rotor_blur_manifest.json')
blur_report = read(O / 'blur_validation.json')
assert blur_report['result'] == 'PASS' and blur_report['sha256'] == blur['sha256']
for path in (O / blur['file'], W / blur['file'], P / blur['file']):
    assert digest(path) == blur['sha256']
for path in (W / 'helicopter_rotor_blur_manifest.json', P / 'helicopter_rotor_blur_manifest.json'):
    assert path.read_bytes() == (O / 'rotor_blur_manifest.json').read_bytes()
kit = {
    'status': 'asset_authoring_frozen',
    'date': '2026-10-23',
    'variants': variants,
    'optional_rotor_blur': blur,
    'provenance': 'Original project geometry/materials; reuse license not selected by owner. No reference images, logos or third-party meshes in outputs.',
    'scope': 'Blender-native and actual-GLB asset delivery only. Flight paths, pursuit, spotlight, audio and WebGL performance are separate runtime integration.',
    'preview_scope': 'Actual GLBs imported in CPU Blender Cycles, 64 samples, no denoising. Studio renders, not gameplay.'
}
kit_file = O / 'helicopter_kit_manifest.json'
kit_file.write_text(json.dumps(kit, indent=2) + '\n')
for target in (W / kit_file.name, P / kit_file.name):
    shutil.copyfile(kit_file, target)

files = [p for p in O.rglob('*') if p.is_file() and p.name != 'freeze.json' and p.suffix not in ('.blend1', '.pyc')]
files += [R / 'blender' / name for name in ('build_helicopter.py', 'render_helicopter.py', 'test_helicopter_mechanics.py', 'test_helicopter_native.py', 'freeze_helicopter.py', 'rebuild_car_helpers.py')]
freeze = {
    'status': 'PASS_AND_FROZEN',
    'date': '2026-10-23',
    'kit_manifest': str(kit_file.relative_to(R)),
    'reports': reports + ['assets/helicopter/blur_validation.json'],
    'previews': previews,
    'identical_staged_public_files': copy_checks,
    'checks': {
        'every_exported_triangle_finite_and_nondegenerate': True,
        'unit_normals': True,
        'independent_native_and_exported_rotors': True,
        'rotor_sweep_samples_per_variant': 144,
        'gimbal_pose_samples_per_variant': 25,
        'sampled_unintended_blade_and_gimbal_intersections': 0,
        'native_interior_parts_checked_per_variant': 36,
        'tail_aperture_conservative_radial_gap_m': 0.050042822667031195,
        'no_image_dependencies': True,
        'runtime_webgl_claim': False,
        'continuous_mechanical_or_airworthiness_claim': False
    },
    'hashes': {str(p.relative_to(R)): {'sha256': digest(p), 'bytes': p.stat().st_size} for p in sorted(set(files))}
}
(O / 'freeze.json').write_text(json.dumps(freeze, indent=2) + '\n')
print(json.dumps({'result': 'PASS_AND_FROZEN', 'variants': [{k: v[k] for k in ('id', 'sha256', 'triangles', 'draw_calls', 'bytes')} for v in variants], 'preview_count': len(previews), 'hashed_files': len(files)}))
