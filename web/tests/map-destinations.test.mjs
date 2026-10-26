import assert from'node:assert/strict';
import fs from'node:fs';
import{MAP_DESTINATIONS}from'../src/map-destinations.js';
import{TRACKS,SURFACE_TEST_TRACK}from'../src/tracks.js';
const tracks={...TRACKS,'surface-test':SURFACE_TEST_TRACK},assets=new URL('../public/assets/',import.meta.url),provenance=JSON.parse(fs.readFileSync(new URL('map-previews/provenance.json',assets)));
assert.equal(MAP_DESTINATIONS.length,11);assert.equal(new Set(MAP_DESTINATIONS.map(d=>d.id)).size,11);assert.equal(new Set(MAP_DESTINATIONS.map(d=>d.track+':'+d.startS)).size,11);
for(const[id,track]of Object.entries(tracks)){
 const world=JSON.parse(fs.readFileSync(new URL(track.file,assets))),destinations=MAP_DESTINATIONS.filter(d=>d.track===id);assert.equal(destinations.length,world.explore_starts.length,'Every canonical start has one card');
 for(const start of world.explore_starts){const d=destinations.find(d=>d.startS===start.s);assert(d,'Canonical start omitted');assert.equal(d.name,start.name);const bytes=fs.readFileSync(new URL('map-previews/'+d.id+'.png',assets));assert.equal(bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a');assert.equal(bytes.readUInt32BE(16),512);assert.equal(bytes.readUInt32BE(20),512);const proof=provenance.previews.find(p=>p.id===d.id);assert(proof);assert.equal(proof.track,id);assert.equal(proof.startS,d.startS);assert.equal(proof.canonicalStart,start.name);assert(proof.position.length===3&&proof.position.every(Number.isFinite)&&proof.target.length===3&&proof.target.every(Number.isFinite));}
 if(id==='surface-test')assert.equal(world.free_drive_only,true);
}
assert.equal(MAP_DESTINATIONS.find(d=>d.id==='metro-market').startS,2008);
assert.deepEqual(fs.readdirSync(new URL('map-previews/',assets)).filter(f=>f.endsWith('.png')).sort(),MAP_DESTINATIONS.map(d=>d.id+'.png').sort());
console.log('PASS exactly eleven unique canonical destination/start mappings across three worlds, complete coverage, 512px preview inventory/provenance and experimental free-drive constraint.');
