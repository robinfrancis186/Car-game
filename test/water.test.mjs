import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { createWaterQuery } from '../shared/water.js';

const data = JSON.parse(await readFile(new URL('../data/water.json', import.meta.url)));
const isWater = createWaterQuery(data);

test('water data preserves frozen authored material selection and Float32 precision', () => {
  assert.equal(data.source, 'Course_Water.glb');
  assert.match(data.sourceSha256, /^[a-f0-9]{64}$/);
  assert.equal(data.triangles.length, 1229);
  assert.deepEqual(data.meshes.map(m=>m.material), ['WEB_Course_IndianOcean']);
  assert.deepEqual(data.excludedMaterials, ['WEB_Course_SurfFoam']);
  assert.equal(data.triangles[0][1], -0.18000000715255737);
});

test('all 1229 authored water triangle centroids hit; distant land and invalid inputs do not', () => {
  for (const t of data.triangles) assert.equal(isWater((t[0]+t[3]+t[6])/3, (t[2]+t[5]+t[8])/3), true);
  assert.equal(isWater(1e6,1e6), false);
  assert.equal(isWater(NaN,0), false);
  assert.equal(isWater(0,Infinity), false);
  assert.equal(isWater('0',0), false);
});

test('downward-ray geometry includes shared triangle edges and rejects outside or above ray origin', () => {
  const query = triangles => createWaterQuery({schemaVersion:1,rayOriginY:30,triangles});
  const q=query([[0,0,0, 10,0,0, 0,0,10]]);
  assert.equal(q(0,0),true);
  assert.equal(q(5,5),true);
  assert.equal(q(5.01,5.01),false);
  assert.equal(query([[0,31,0,10,31,0,0,31,10]])(1,1),false);
  assert.equal(query([[0,30,0,10,30,0,0,30,10]])(1,1),true);
  assert.equal(query([[0,0,0,0,1,0,0,2,0]])(0,0),false);
});

test('water query rejects malformed authoring data', () => {
  assert.throws(()=>createWaterQuery({}), /Invalid authored/);
  assert.throws(()=>createWaterQuery({schemaVersion:1,rayOriginY:30,triangles:[[0,0,NaN]]}), /Invalid water triangle/);
});
