import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const hashFiles=(names)=>{const h=createHash('sha256');for(const name of names){h.update(name);h.update(readFileSync(new URL(name,import.meta.url)));}return h.digest('hex');};
const json=n=>JSON.parse(readFileSync(new URL('../data/'+n,import.meta.url)));
export function loadData(){return {world:json('course_runtime.json'),furniture:json('furniture_colliders.json'),infrastructure:json('infrastructure_colliders.json'),water:json('water.json')};}
export function getManifest(){return {protocolVersion:1,physicsVersion:'v10-stock-noncontact-alpha1-'+hashFiles(['../shared/gameplay.js','../shared/garage.js','../shared/world.mjs','../shared/water.js']).slice(0,16),trackHash:hashFiles(['../data/course_runtime.json','../data/furniture_colliders.json','../data/infrastructure_colliders.json','../data/water.json']),tickRate:60,snapshotRate:20,rules:{maxPlayers:2,stock:true,contact:false,traffic:false,flight:false,ultraBoost:false,payouts:false}};}
