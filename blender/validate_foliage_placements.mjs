/** CPU deterministic placement proof, not a browser/FPS benchmark. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const out=root+'assets/foliage_detail';
const {selectTeaDetailPlacements,buildTeaPlacementIndex,sampleTeaTerrain}=await import(new URL('../assets/foliage_detail/tea_placements_reference.js',import.meta.url));
const w=JSON.parse(fs.readFileSync(root+'assets/web/course_runtime_highlands.json'));
const m=JSON.parse(fs.readFileSync(out+'/tea_detail_rows.json'));
const fixture=JSON.parse(fs.readFileSync(out+'/tea_placement_fixture.json'));
const index=buildTeaPlacementIndex(m);
const a=selectTeaDetailPlacements(m,w.terrain_grid,{...fixture.query,index});
assert.deepEqual(a,fixture.result);
assert.equal(a.placements.length,20);
let samples=0,error=0,maxHigh=0,maxBalanced=0;
for(let i=0;i<w.route_points.length;i+=45){
 for(const [radius,maxInstances] of [[85,1250],[50,500]]){
  const result=selectTeaDetailPlacements(m,w.terrain_grid,{center:w.route_points[i],radius,maxInstances,index});
  assert(result.placements.length<=maxInstances);
  assert.equal(new Set(result.placements.map(p=>p.id)).size,result.placements.length);
  assert(result.coverage_radius_m>=0&&result.coverage_radius_m<=radius);
  if(maxInstances===1250)maxHigh=Math.max(maxHigh,result.selected_triangles);else maxBalanced=Math.max(maxBalanced,result.selected_triangles);
  for(const p of result.placements){samples++;const e=Math.abs(p.position[1]-sampleTeaTerrain(w.terrain_grid,p.position[0],p.position[2]));error=Math.max(error,e);assert(p.position.every(Number.isFinite));assert(p.distance_m<=radius+1e-8);}
 }
}
assert.equal(error,0);
const off=selectTeaDetailPlacements(m,w.terrain_grid,{center:[1200,150,-900],radius:85,maxInstances:1250,index});assert.equal(off.coverage_radius_m,0);
const report={scope:'Pure JS selector/triangle terrain tests, not browser performance.',fixture_count:20,fixture_exact:true,root_samples:samples,root_max_height_error:error,max_high_triangles:maxHigh,max_balanced_triangles:maxBalanced,off_road_fade_radius:off.coverage_radius_m,passed:true};
fs.writeFileSync(out+'/placement_validation.json',JSON.stringify(report,null,2));console.log(report);
