/** Original course catalogue. The coastal X/Z route derives from OSM; the highland course is authored fiction. */
export const TRACKS=Object.freeze({
 coast:Object.freeze({id:'coast',name:'HOT COAST',subtitle:'METRO / FLYOVER / BACKWATERS',file:'course_runtime.json',credit:'OSM-derived coast, fictional Kerala districts'}),
 highlands:Object.freeze({id:'highlands',name:'HIGHLAND RUN',subtitle:'HIGHWAY / TEA HILLS / HAIRPINS',file:'course_runtime_highlands.json',credit:'Original fictional Kerala-inspired mountain course'})
});
export const SURFACE_TEST_TRACK=Object.freeze({id:'surface-test',name:'HARBOUR WALL RUN',subtitle:'SOLO SURFACE TEST / 90° BANK',file:'course_runtime_surface_test.json',credit:'Original fictional test corridor',experimentalSurface:true});
export function trackFromSearch(search=''){const id=new URLSearchParams(search).get('track');return id===SURFACE_TEST_TRACK.id?SURFACE_TEST_TRACK:Object.hasOwn(TRACKS,id)?TRACKS[id]:TRACKS.coast;}
export function routeLength(route){let n=0;for(let i=1;i<route.length;i++)n+=Math.hypot(route[i].x-route[i-1].x,route[i].z-route[i-1].z);return n;}
export function eventSlice(track,world,id,length,start=0){
 if(track.experimentalSurface)return {startS:Math.max(20,Math.min(length-30,Number(start)||30)),endS:length,distance:'SOLO TEST',risk:'NO RACE / NO COIN REWARDS'};
 if(id==='free-drive')return {startS:Math.max(0,Math.min(length-30,Number(start)||0)),endS:length,distance:'OPEN COURSE',risk:'NO CLOCK / NO PURSUIT'};
 const legacy={ 'coast-sprint':{startS:2200,endS:3350},'hot-pursuit':{startS:2200,endS:4350},'time-attack':{startS:0,endS:length} };
 const fallback=track.id==='coast'?legacy[id]:{startS:0,endS:length};
 const range={...fallback,...world?.event_slices?.[id]};
 range.startS=Math.max(0,Math.min(length-30,range.startS||0));range.endS=Math.max(range.startS+20,Math.min(length,range.endS||length));
 return {...range,distance:`${((range.endS-range.startS)/1000).toFixed(2)} KM`,risk:id==='coast-sprint'?'3 RIVALS / PATROL WATCH':id==='hot-pursuit'?'2 UNITS / ACTIVE PURSUIT':'SOLO / AGAINST THE CLOCK'};
}
export function worldPhysicsOptions(world={}){return {ramps:world.ramps||[],airTraffic:world.air_traffic||false,elevatedCorridors:world.elevated_corridors||[],terrainGrid:world.terrain_grid,roadSections:world.road_sections||[],terrainY:world.terrain_y??-.04};}
