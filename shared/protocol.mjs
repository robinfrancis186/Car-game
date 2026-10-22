export const NEUTRAL=Object.freeze({throttle:0,steer:0,brake:true,boost:false,recover:false});
export function exact(obj,keys){return !!obj&&typeof obj==='object'&&!Array.isArray(obj)&&Object.keys(obj).every(k=>keys.includes(k))&&keys.every(k=>Object.hasOwn(obj,k));}
export function validControls(c){return exact(c,['throttle','steer','brake','boost','recover'])&&['throttle','steer'].every(k=>typeof c[k]==='number'&&Number.isFinite(c[k])&&Math.abs(c[k])<=1)&&['brake','boost','recover'].every(k=>typeof c[k]==='boolean');}
export function versionError(m,manifest){return m.protocolVersion!==manifest.protocolVersion?'PROTOCOL_MISMATCH':m.physicsVersion!==manifest.physicsVersion?'PHYSICS_MISMATCH':m.trackHash!==manifest.trackHash?'TRACK_MISMATCH':null;}
export const JOIN_KEYS=['type','name','protocolVersion','physicsVersion','trackHash'];
export function validName(s){return typeof s==='string'&&s.length>=1&&s.length<=24&&!/[\x00-\x1f\x7f<>\u202a-\u202e\u2066-\u2069]/.test(s);}
