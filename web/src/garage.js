/** Original local-only progression. No accounts, paid currency or server economy. */
export const STARTER_CREDITS=1200,MAX_UPGRADE_LEVEL=3;
export const UPGRADE_COSTS=Object.freeze([300,600,1000]);
export const CAR_IDS=Object.freeze(['red','silver']);
export const UPGRADE_CATALOG=Object.freeze({
 speed:Object.freeze({label:'TOP SPEED',description:'+3% speed limits per level'}),
 acceleration:Object.freeze({label:'ACCELERATION',description:'+5% forward motor acceleration per level'}),
 handling:Object.freeze({label:'CORNER GRIP',description:'+3% paved-road grip and lateral damping per level'}),
 boost:Object.freeze({label:'BOOST SYSTEM',description:'More efficient regular boost and quicker ultra recharge'})
});
const bounded=(v,lo,hi,fallback=0)=>typeof v==='number'&&Number.isFinite(v)?Math.max(lo,Math.min(hi,Math.floor(v))):fallback;
const validRunId=id=>typeof id==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(id);
export function sanitizeUpgrades(raw={}){const result={};for(const key of Object.keys(UPGRADE_CATALOG))result[key]=bounded(raw&&Object.hasOwn(raw,key)?raw[key]:0,0,MAX_UPGRADE_LEVEL);return result;}
export function getUpgradeStats(raw={}){const u=sanitizeUpgrades(raw),speed=1+u.speed*.03,boost=1+u.boost*.1;return{
 topSpeedMps:68*speed,regularBoostMaxSpeedMps:83*speed,ultraBoostMaxSpeedMps:97*speed,
 accelerationMultiplier:1+u.acceleration*.05,gripMultiplier:1+u.handling*.03,
 boostEfficiency:boost,boostRechargeMultiplier:1+u.boost*.08,
 ultraDuration:1.25*(1+u.boost*.08),ultraCooldownSeconds:8/boost,ultraRechargePerSecond:.06*boost
};}
export function createProfile(){return{schemaVersion:1,credits:STARTER_CREDITS,cars:{red:sanitizeUpgrades(),silver:sanitizeUpgrades()},awardedRuns:[]};}
export const resetProfile=createProfile;
export function validateProfile(raw){
 const p=createProfile();if(!raw||typeof raw!=='object'||Array.isArray(raw))return p;
 p.credits=bounded(raw.credits,0,999999,STARTER_CREDITS);
 for(const id of CAR_IDS)p.cars[id]=sanitizeUpgrades(raw.cars&&Object.hasOwn(raw.cars,id)?raw.cars[id]:{});
 if(Array.isArray(raw.awardedRuns))p.awardedRuns=[...new Set(raw.awardedRuns.slice(-256).filter(validRunId))];return p;
}
export function getCarModifiers(profile,carId){const p=validateProfile(profile),u=p.cars[CAR_IDS.includes(carId)?carId:'red'];return{upgrades:{...u},...getUpgradeStats(u)};}
export function purchaseUpgrade(profile,carId,stat){
 const p=validateProfile(profile);if(!CAR_IDS.includes(carId)||!Object.hasOwn(UPGRADE_CATALOG,stat))return{ok:false,profile:p,reason:'invalid-upgrade',cost:0,level:0};
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
 const p=validateProfile(profile);if(!validRunId(runId))return{ok:false,profile:p,reward:0,reason:'invalid-run'};
 if(p.awardedRuns.includes(runId))return{ok:false,profile:p,reward:0,reason:'already-awarded'};
 const reward=rewardForResult(result);if(!reward)return{ok:false,profile:p,reward:0,reason:'no-reward'};
 const credited=Math.min(reward,999999-p.credits);p.credits+=credited;p.awardedRuns=[...p.awardedRuns,runId].slice(-256);return{ok:true,profile:p,reward:credited,reason:null};
}
