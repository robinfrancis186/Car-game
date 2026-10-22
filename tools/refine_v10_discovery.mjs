/** Metadata-only safe Explore destinations and original scenic inspection cameras.
 * Re-run after base course export. Geometry, route, terrain and collider bytes are untouched. */
import fs from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(new URL('..',import.meta.url).pathname);
const settings={
 'course_runtime.json':[
  {s:5,label:'COASTAL VILLAGE',position:[30,3,-70],camera_offset:[25,14,30]},
  {s:2000,label:'ELEVATED METRO',position:[-897.886,15,-1630.970],camera_offset:[-30,1,3],camera_fov:40,transit_id:'coast_metro_shuttle'},
  {s:2415,label:'SHIKARA LANDING',position:[-1193.823,1.5,-1727.367],camera_offset:[23,9,18]},
  {s:2530,label:'SKYLINE FLYOVER',route_s:2730,camera_offset:[45,24,30]},
  {s:3180,label:'WATER TRANSIT FERRY',position:[-1530,2.5,-2380],camera_offset:[32,16,24],transit_id:'backwater_ferry_shuttle'},
  {s:4035,label:'HARBOUR AVENUE',route_s:4090,camera_offset:[22,15,28]}
 ],
 'course_runtime_highlands.json':[
  {s:30,label:'DIVIDED HIGHWAY',route_s:250,camera_offset:[-20,24,35]},
  {s:1105,label:'TEA ESTATE',route_s:1270,camera_offset:[40,26,32]},
  {s:1880,label:'ESTATE SWITCHBACKS',route_s:2160,camera_offset:[55,35,40]},
  {s:3650,label:'BIRD ROCK LOOKOUT',position:[490,107,-850],camera_offset:[40,18,30],portrait_distance_scale:2.6}
 ]
};
function at(route,s){let d=0;for(let i=1;i<route.length;i++){const a=route[i-1],b=route[i],len=Math.hypot(b[0]-a[0],b[2]-a[2]);if(d+len>=s){const t=(s-d)/len;return a.map((v,j)=>v+(b[j]-v)*t);}d+=len;}return route.at(-1);}
for(const [file,entries] of Object.entries(settings)){
 const source=path.join(root,'web/public/assets',file),world=JSON.parse(await fs.readFile(source,'utf8'));
 world.explore_starts=world.explore_starts.map((entry,i)=>{const s=entries[i],position=s.position||at(world.route_points,s.route_s).map((n,k)=>n+(k===1?2:0));return {...entry,s:s.s,landmark:{label:s.label,position,camera_offset:s.camera_offset,...(s.camera_fov?{camera_fov:s.camera_fov}:{}),...(s.portrait_distance_scale?{portrait_distance_scale:s.portrait_distance_scale}:{}),...(s.transit_id?{transit_id:s.transit_id}:{})}};});
 if(world.world?.explore_starts)world.world.explore_starts=world.explore_starts;
 const serialized=JSON.stringify(world);for(const dir of ['web/public/assets','assets/web',...(file.includes('highlands')?['assets/highlands']:[])])await fs.writeFile(path.join(root,dir,file),serialized);
 console.log(file,world.explore_starts.map(e=>`${e.name}: ${e.s}m`).join(' | '));
}
