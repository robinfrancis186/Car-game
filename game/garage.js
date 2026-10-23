/** Original device-local progression. No accounts, paid currency or online authority. */
export const STARTER_CREDITS=0,MAX_UPGRADE_LEVEL=3;
export const UPGRADE_COSTS=Object.freeze([300,600,1000]);
export const CAR_CATALOG=Object.freeze({
 red:Object.freeze({name:'CRIMSON ROADSTER',price:0,maxSteer:.57,topSpeedMps:68,acceleration:1,grip:1,mass:1450,statsLabel:'BALANCED ELECTRIC'}),
 silver:Object.freeze({name:'SILVER ROADSTER',price:0,maxSteer:.4,topSpeedMps:68,acceleration:1,grip:1,mass:1450,statsLabel:'THRUSTER CONCEPT'}),
 touring:Object.freeze({name:'AZURE TOURING GT',price:5000,maxSteer:.45,topSpeedMps:66.5,acceleration:1.02,grip:1.07,mass:1380,statsLabel:'GRIP-FOCUSED COUPE'})
});
export const CAR_IDS=Object.freeze(Object.keys(CAR_CATALOG));
export const UPGRADE_CATALOG=Object.freeze({
 speed:Object.freeze({label:'TOP SPEED',description:'+3% speed limits per level'}),
 acceleration:Object.freeze({label:'ACCELERATION',description:'+5% forward motor acceleration per level'}),
 handling:Object.freeze({label:'CORNER GRIP',description:'+3% paved-road grip and lateral damping per level'}),
 boost:Object.freeze({label:'BOOST SYSTEM',description:'More efficient regular boost and quicker ultra recharge'})
});
const bounded=(v,lo,hi,fallback=0)=>typeof v==='number'&&Number.isFinite(v)?Math.max(lo,Math.min(hi,Math.floor(v))):fallback;
const validRunId=id=>typeof id==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(id);
const validCar=id=>CAR_IDS.includes(id);
export function sanitizeUpgrades(raw={}){const result={};for(const key of Object.keys(UPGRADE_CATALOG))result[key]=bounded(raw&&Object.hasOwn(raw,key)?raw[key]:0,0,MAX_UPGRADE_LEVEL);return result;}
export function getUpgradeStats(raw={},carId='red'){
 const vehicleId=validCar(carId)?carId:'red',base=CAR_CATALOG[vehicleId],u=sanitizeUpgrades(raw),speed=(1+u.speed*.03)*base.topSpeedMps/68,boost=1+u.boost*.1;
 return {vehicleId,maxSteer:base.maxSteer,mass:base.mass,topSpeedMps:68*speed,regularBoostMaxSpeedMps:83*speed,ultraBoostMaxSpeedMps:97*speed,
 accelerationMultiplier:base.acceleration*(1+u.acceleration*.05),gripMultiplier:base.grip*(1+u.handling*.03),
 boostEfficiency:boost,boostRechargeMultiplier:1+u.boost*.08,ultraDuration:1.25*(1+u.boost*.08),ultraCooldownSeconds:8/boost,ultraRechargePerSecond:.06*boost};
}
export function createProfile(){return{schemaVersion:2,credits:STARTER_CREDITS,cars:Object.fromEntries(CAR_IDS.map(id=>[id,sanitizeUpgrades()])),ownedCars:['red','silver'],selectedCar:'red',awardedRuns:[]};}
export const resetProfile=createProfile;
export function validateProfile(raw){
 const p=createProfile();if(!raw||typeof raw!=='object'||Array.isArray(raw))return p;
 // Version-one saves retain every earned/starter coin and both existing cars.
 p.credits=bounded(raw.credits,0,999999,STARTER_CREDITS);
 if(Array.isArray(raw.ownedCars))for(const id of raw.ownedCars)if(validCar(id)&&!p.ownedCars.includes(id))p.ownedCars.push(id);
 for(const id of CAR_IDS)p.cars[id]=sanitizeUpgrades(p.ownedCars.includes(id)&&raw.cars&&Object.hasOwn(raw.cars,id)?raw.cars[id]:{});
 if(p.ownedCars.includes(raw.selectedCar))p.selectedCar=raw.selectedCar;
 if(Array.isArray(raw.awardedRuns))p.awardedRuns=[...new Set(raw.awardedRuns.slice(-256).filter(validRunId))];return p;
}
export function isCarOwned(profile,carId){return validCar(carId)&&validateProfile(profile).ownedCars.includes(carId);}
export function selectOwnedCar(profile,carId){const p=validateProfile(profile);if(!validCar(carId))return{ok:false,profile:p,reason:'invalid-car'};if(!p.ownedCars.includes(carId))return{ok:false,profile:p,reason:'car-locked'};p.selectedCar=carId;return{ok:true,profile:p,reason:null};}
export function purchaseCar(profile,carId){
 const p=validateProfile(profile);if(!validCar(carId))return{ok:false,profile:p,reason:'invalid-car',cost:0};
 const cost=CAR_CATALOG[carId].price;if(p.ownedCars.includes(carId))return{ok:false,profile:p,reason:'already-owned',cost:0};
 if(p.credits<cost)return{ok:false,profile:p,reason:'insufficient-credits',cost};
 p.credits-=cost;p.ownedCars.push(carId);p.selectedCar=carId;return{ok:true,profile:p,reason:null,cost,carId};
}
export function getCarModifiers(profile,carId){const p=validateProfile(profile),id=validCar(carId)?carId:'red',u=p.cars[id];return{upgrades:{...u},...getUpgradeStats(u,id)};}
export function purchaseUpgrade(profile,carId,stat){
 const p=validateProfile(profile);if(!validCar(carId)||!Object.hasOwn(UPGRADE_CATALOG,stat))return{ok:false,profile:p,reason:'invalid-upgrade',cost:0,level:0};
 if(!p.ownedCars.includes(carId))return{ok:false,profile:p,reason:'car-locked',cost:0,level:0};
 const level=p.cars[carId][stat];if(level>=MAX_UPGRADE_LEVEL)return{ok:false,profile:p,reason:'max-level',cost:0,level};
 const cost=UPGRADE_COSTS[level];if(p.credits<cost)return{ok:false,profile:p,reason:'insufficient-credits',cost,level};
 p.credits-=cost;p.cars[carId][stat]++;return{ok:true,profile:p,reason:null,cost,level:level+1};
}
export function rewardForResult(result){
 if(!result||result.state!=='finished'||!['coast-sprint','hot-pursuit','time-attack'].includes(result.scenario))return 0;
 if(!Number.isInteger(result.position)||result.position<1||result.position>4)return 0;
 return(result.position===1?500:350)+(result.scenario==='hot-pursuit'?100:0);
}
export function awardResult(profile,result,runId){
 const p=validateProfile(profile),none=reason=>({ok:false,profile:p,reward:0,finishReward:0,collectedReward:0,reason});
 if(!validRunId(runId))return none('invalid-run');if(p.awardedRuns.includes(runId))return none('already-awarded');
 const finish=rewardForResult(result);if(!finish)return none('no-reward');
 // Pickups are banked only with a valid completed race. Recovery never pays or
 // resets their run ledger. The local profile is not trusted by multiplayer.
 const collected=bounded(result.collectedCoins,0,600),capacity=999999-p.credits;
 const finishReward=Math.min(finish,capacity),collectedReward=Math.min(collected,capacity-finishReward),reward=finishReward+collectedReward;
 p.credits+=reward;p.awardedRuns=[...p.awardedRuns,runId].slice(-256);return{ok:true,profile:p,reward,finishReward,collectedReward,reason:null};
}
