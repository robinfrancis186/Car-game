#!/usr/bin/env python3
"""Extract the frozen coast's renderer-selected water triangles without a GPU.

Usage: python3 tools/export_water.py public/assets/Course_Water.glb data/water.json
No third-party Python package is required. Only GLB v2 internal-buffer triangle
meshes are accepted. Unsupported sparse/compressed/normalized data fails closed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def multiply(a, b):
    return [sum(a[k * 4 + row] * b[col * 4 + k] for k in range(4))
            for col in range(4) for row in range(4)]


def local_matrix(node):
    if 'matrix' in node:
        matrix = node['matrix']
        if len(matrix) != 16 or not all(math.isfinite(v) for v in matrix):
            raise ValueError('Invalid node matrix')
        return matrix
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    sx, sy, sz = node.get('scale', [1, 1, 1])
    tx, ty, tz = node.get('translation', [0, 0, 0])
    # glTF / Three column-major T * R * S matrix.
    return [(1 - 2*y*y - 2*z*z)*sx, (2*x*y + 2*z*w)*sx, (2*x*z - 2*y*w)*sx, 0,
            (2*x*y - 2*z*w)*sy, (1 - 2*x*x - 2*z*z)*sy, (2*y*z + 2*x*w)*sy, 0,
            (2*x*z + 2*y*w)*sz, (2*y*z - 2*x*w)*sz, (1 - 2*x*x - 2*y*y)*sz, 0,
            tx, ty, tz, 1]


def transform(m, p):
    return [m[row]*p[0] + m[4+row]*p[1] + m[8+row]*p[2] + m[12+row] for row in range(3)]


def extract(source):
    raw = source.read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    if magic != 0x46546c67 or version != 2 or length != len(raw):
        raise ValueError('Expected complete GLB v2')
    chunks = {}
    offset = 12
    while offset < len(raw):
        size, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if offset + size > len(raw):
            raise ValueError('Truncated chunk')
        chunks[kind] = raw[offset:offset+size]
        offset += size
    doc = json.loads(chunks[0x4e4f534a])
    blob = chunks[0x004e4942]
    if len(doc['buffers']) != 1 or 'uri' in doc['buffers'][0]:
        raise ValueError('Only one internal GLB buffer is supported')

    def accessor(index):
        a = doc['accessors'][index]
        if a.get('sparse') or a.get('normalized'):
            raise ValueError('Sparse/normalized accessors are not supported')
        view = doc['bufferViews'][a['bufferView']]
        if view.get('extensions') or view.get('buffer', 0) != 0:
            raise ValueError('Compressed/external views are not supported')
        kind = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']]
        width = {'SCALAR': 1, 'VEC3': 3}[a['type']]
        fmt = '<' + kind * width
        size = struct.calcsize(fmt)
        stride = view.get('byteStride', size)
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        if stride < size or start + (a['count']-1)*stride + size > view.get('byteOffset', 0)+view['byteLength']:
            raise ValueError('Accessor exceeds buffer view')
        values = [list(struct.unpack_from(fmt, blob, start+i*stride)) for i in range(a['count'])]
        if not all(math.isfinite(v) for p in values for v in p):
            raise ValueError('Non-finite geometry')
        return values

    triangles, selected, excluded = [], [], []

    def visit(index, parent, ancestors):
        if index in ancestors:
            raise ValueError('Cyclic nodes')
        node = doc['nodes'][index]
        matrix = multiply(parent, local_matrix(node))
        if 'mesh' in node:
            mesh = doc['meshes'][node['mesh']]
            for primitive in mesh['primitives']:
                material = doc.get('materials', [])[primitive['material']]
                name = material.get('name', '')
                if not re.search(r'ocean|water', name, re.I):
                    excluded.append(name)
                    continue
                if primitive.get('mode', 4) != 4 or primitive.get('extensions'):
                    raise ValueError('Only uncompressed TRIANGLES are supported')
                positions = [transform(matrix, p) for p in accessor(primitive['attributes']['POSITION'])]
                indices = [p[0] for p in accessor(primitive['indices'])] if 'indices' in primitive else list(range(len(positions)))
                if len(indices) % 3:
                    raise ValueError('Incomplete triangle')
                double_sided = bool(material.get('doubleSided', False))
                count = 0
                for i in range(0, len(indices), 3):
                    a, b, c = [positions[j] for j in indices[i:i+3]]
                    normal_y = (b[2]-a[2])*(c[0]-a[0]) - (b[0]-a[0])*(c[2]-a[2])
                    # Three's GLTF FrontSide material rejects downward-facing
                    # triangles from the renderer's downward ray. Vertical
                    # triangles cannot intersect a non-collinear vertical ray.
                    if abs(normal_y) < 1e-12 or (not double_sided and normal_y <= 0):
                        continue
                    triangles.append(a+b+c)
                    count += 1
                selected.append({'node': node.get('name'), 'material': name,
                                 'doubleSided': double_sided, 'triangles': count})
        for child in node.get('children', []):
            visit(child, matrix, ancestors | {index})

    for root in doc['scenes'][doc.get('scene', 0)].get('nodes', []):
        visit(root, IDENTITY, set())
    if not triangles:
        raise ValueError('No downward-ray-visible water found')
    return {
        'schemaVersion': 1,
        'source': source.name,
        'sourceSha256': hashlib.sha256(raw).hexdigest(),
        'provenance': 'Frozen V10 authored coast GLB; source water geometry, not inferred coastline polygons.',
        'selection': 'course_meshes file /Water/i and primitive material /ocean|water/i; active glTF scene world transforms; front-face downward ray',
        'rayOriginY': 30,
        'units': 'metres; +Y up; [ax,ay,az,bx,by,bz,cx,cy,cz]',
        'precision': 'Original Float32 GLB coordinates exported losslessly to JSON numbers; barycentric query epsilon 1e-10. No rendered wave displacement, GPU, or remote network acceptance implied.',
        'meshes': selected,
        'excludedMaterials': sorted(set(excluded)),
        'triangles': triangles,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = extract(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(json.dumps({'output': str(args.output), 'triangles': len(result['triangles']), 'sourceSha256': result['sourceSha256']}))


if __name__ == '__main__':
    main()
