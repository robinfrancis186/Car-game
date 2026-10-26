/** Skinned CC0 anatomical humans and original CPO garments; capture state lives in the model. */
import * as THREE from 'three';
import {CaptureHuman} from './capture-human.js';
import {captureEase,sampleCapturePath} from './police-capture.js';
const mix=(a,b,t)=>a+(b-a)*t;
export class PoliceCaptureScene{
 constructor(scene,templates){
  this.group=new THREE.Group();this.group.name='Police capture sequence';this.group.visible=false;scene.add(this.group);
  this.officers=[0,1].map(i=>new CaptureHuman(templates.officer,`Capture officer ${i+1}`));this.driver=new CaptureHuman(templates.driver,'Captured driver');for(const p of [...this.officers,this.driver])this.group.add(p.root);
  this.doors=[-1,1].map(side=>{const root=new THREE.Group();root.name=`Patrol exit door ${side}`;const paint=new THREE.MeshStandardMaterial({color:'#d7dedc',metalness:.55,roughness:.26}),glass=new THREE.MeshStandardMaterial({color:'#152b35',metalness:.2,roughness:.13});
   for(const [size,y,mat]of [[[1.35,.46,.045],.64,paint],[[1.25,.23,.025],.99,glass]]){const mesh=new THREE.Mesh(new THREE.BoxGeometry(...size),mat);mesh.position.set(-.675,y,0);mesh.castShadow=true;root.add(mesh);}this.group.add(root);return {root,side};});
  this.cuffs=new THREE.Group();this.cuffs.name='Visible secured wrists';const metal=new THREE.MeshStandardMaterial({color:'#c5d1d5',metalness:.9,roughness:.23});for(const x of [-.08,.08]){const ring=new THREE.Mesh(new THREE.TorusGeometry(.055,.014,6,12),metal);ring.position.x=x;this.cuffs.add(ring);}const link=new THREE.Mesh(new THREE.BoxGeometry(.11,.022,.022),metal);this.cuffs.add(link);this.driver.root.add(this.cuffs);
 }
 update(model,{menu=false,quality='high'}={}){
  const c=model.capture;this.group.visible=!menu&&!!c&&['capturing','busted'].includes(model.state);if(!this.group.visible)return;
  const lod=quality==='high'?'near':'mobile';for(const p of [...this.officers,this.driver])p.useLOD(lod);
  const t=c.elapsed,exit=captureEase(t/1.4),approach=captureEase((t-1.4)/3.4),secure=captureEase((t-5.2)/1.4);
  this.doors.forEach(({root,side})=>{const co=Math.cos(c.cop.heading),si=Math.sin(c.cop.heading);root.position.set(c.cop.x+co*.7-si*side*.94,c.cop.y,c.cop.z+si*.7+co*side*.94);root.rotation.y=-c.cop.heading+side*captureEase(t/.5)*(1-captureEase((t-1.2)/.6))*1.15;root.visible=t<1.8;});
  this.officers.forEach((officer,i)=>{const track=c.officers[i],point=t<1.4?{x:mix(track.start.x,track.path[0].x,exit),y:mix(track.start.y,track.path[0].y,exit),z:mix(track.start.z,track.path[0].z,exit),heading:-c.cop.heading+(track.door>0?0:Math.PI)}:sampleCapturePath(track.path,approach);
   officer.root.position.set(point.x,point.y,point.z);officer.root.rotation.y=t<4.8?point.heading:Math.atan2(c.suspect.x-point.x,c.suspect.z-point.z);officer.root.visible=t>.15;
   officer.pose({walk:t>1.4&&t<4.8?1:0,time:t,seated:1-exit});
  });
  const out=captureEase((t-3.3)/1.1),from=c.player,driver=this.driver;
  driver.root.visible=t>3.3;driver.root.position.set(mix(from.x,c.suspect.x,out),mix(from.y,c.suspect.y,out),mix(from.z,c.suspect.z,out));
  driver.root.rotation.y=mix(Math.PI/2-c.player.heading,-c.player.heading+(c.side>0?Math.PI:0),out);
  driver.pose({seated:1-out,surrender:out*(1-secure),secured:secure});
  this.group.updateMatrixWorld(true);
  const wrists=['l','r'].map(side=>driver.joint('hand_'+side));
  const arresting=this.officers[0];arresting.contactErrors=wrists.map((target,i)=>arresting.grasp(i?'r':'l',target,target.clone().sub(driver.joint('lowerarm_'+(i?'r':'l'))).normalize(),secure));
  // Restraints are centered on the actual animated wrists, not a fixed prop target.
  this.cuffs.visible=t>=6.35;
  this.cuffs.position.copy(driver.root.worldToLocal(wrists[0].clone().add(wrists[1]).multiplyScalar(.5)));
  this.cuffs.rotation.y=0;
  this.diagnostics={lod,contactMeasure:'officer palm center to calibrated wrist surface target; skinned surface contact checked',contactErrors:arresting.contactErrors,driverWristSeparation:wrists[0].distanceTo(wrists[1])};

 }
 camera(c,aspect=1){
  if(c.elapsed>=4.8){const h=c.player.heading,scale=Math.max(1,.65/aspect),p=c.suspect;return {position:[p.x+(Math.cos(h)*5-Math.sin(h)*c.side*3.5)*scale,p.y+2.7*scale,p.z+(Math.sin(h)*5+Math.cos(h)*c.side*3.5)*scale],target:[p.x,p.y+1.05,p.z],fov:53};}
  const x=(c.player.x+c.cop.x)/2,z=(c.player.z+c.cop.z)/2,y=Math.max(c.player.y,c.cop.y),h=c.player.heading,scale=Math.max(1,.95/aspect);
  return {position:[x+(-Math.cos(h)*6-Math.sin(h)*c.side*10)*scale,y+5*scale,z+(-Math.sin(h)*6+Math.cos(h)*c.side*10)*scale],target:[x,y+.8,z],fov:53};
 }
 dispose(){const geometries=new Set(),materials=new Set();this.group.traverse(o=>{if(o.isMesh){geometries.add(o.geometry);materials.add(o.material);}});for(const g of geometries)g.dispose();for(const m of materials)m.dispose();this.group.removeFromParent();}
}
