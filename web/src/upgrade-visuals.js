/** Per-instance cosmetic finishes reflect real installed tuning, never change ownership or physics. */
import {sanitizeUpgrades,BRAKE_CALIPER_COLORS} from './garage.js';
const list=m=>Array.isArray(m)?m:[m];
export function installUpgradeVisuals(car){
 const groups={calipers:[],aero:[],rims:[],paint:[],nozzles:[]};
 car.group.traverse(o=>{if(!o.isMesh)return;let caliper=false;for(let n=o;n;n=n.parent)if(/^Caliper_/.test(n.name)){caliper=true;break;}
 for(const m of list(o.material)){const name=m.name.toLowerCase();if(caliper)groups.calipers.push(m);else if(/carbon|aero|graphite aerodynamic/.test(name))groups.aero.push(m);else if(/alloy|aluminum|rim edges/.test(name))groups.rims.push(m);else if(/crimson multi-coat/.test(name))groups.paint.push(m);else if(/nozzle|titanium/.test(name))groups.nozzles.push(m);}
 });
 for(const key of Object.keys(groups))groups[key]=[...new Set(groups[key])].map(material=>({material,color:material.color.clone(),roughness:material.roughness,metalness:material.metalness,env:material.envMapIntensity}));
 car.upgradeVisuals=groups;car.upgradeVisualKey=null;return groups;
}
export function applyUpgradeVisuals(car,raw={}){
 const u=sanitizeUpgrades(raw),key=JSON.stringify(u);if(car.upgradeVisualKey===key)return false;
 if(!car.upgradeVisuals)installUpgradeVisuals(car);car.upgradeVisualKey=key;car.visualUpgrades={...u};
 const colors=BRAKE_CALIPER_COLORS;
 for(const{material:m}of car.upgradeVisuals.calipers){m.color.set(colors[u.braking||0]);m.roughness=.32;m.metalness=.35;}
 for(const b of car.upgradeVisuals.aero){const m=b.material;m.color.copy(b.color);if(u.handling)m.color.lerpColors(b.color,b.color.clone().set('#455766'),u.handling*.17);m.roughness=Math.max(.18,b.roughness-u.handling*.045);}
 for(const b of car.upgradeVisuals.rims){b.material.color.copy(b.color);b.material.roughness=Math.max(.16,b.roughness-u.speed*.035);b.material.metalness=Math.min(1,b.metalness+u.speed*.04);}
 for(const b of car.upgradeVisuals.paint){b.material.roughness=Math.max(.18,b.roughness-u.acceleration*.018);b.material.envMapIntensity=b.env+u.acceleration*.06;}
 for(const b of car.upgradeVisuals.nozzles){b.material.color.copy(b.color);if(u.boost)b.material.color.lerpColors(b.color,b.color.clone().set(u.boost===3?'#9a7fb2':'#ae9b75'),u.boost*.12);}
 car.aeroTrimAngle=(u.handling||0)*.012;return true;
}
