/** Original articulated project geometry, with no third-party character assets. */
import * as THREE from 'three';
import {captureEase,sampleCapturePath} from './police-capture.js';
const mix=(a,b,t)=>a+(b-a)*t;
function person(officer,index){
 const root=new THREE.Group();root.name=officer?`Capture officer ${index+1}`:'Captured driver';
 const cloth=new THREE.MeshStandardMaterial({color:officer?'#ae956d':'#386c81',roughness:.94}),dark=new THREE.MeshStandardMaterial({color:'#182329',roughness:.72}),skin=new THREE.MeshStandardMaterial({color:index===1?'#875638':'#b77b53',roughness:.87}),metal=new THREE.MeshStandardMaterial({color:'#c8b680',metalness:.7,roughness:.35});
 const materials=[cloth,dark,skin,metal],box=(parent,size,position,mat)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(...size),mat);m.position.set(...position);m.castShadow=true;m.receiveShadow=true;parent.add(m);return m;};
 const sphere=(parent,r,position,mat)=>{const m=new THREE.Mesh(new THREE.SphereGeometry(r,10,8),mat);m.position.set(...position);m.castShadow=true;parent.add(m);return m;};
 box(root,[.4,.5,.24],[0,1.19,0],cloth);box(root,[.39,.10,.25],[0,.92,0],dark);sphere(root,.145,[0,1.64,0],skin);sphere(root,.045,[0,1.62,.135],skin);
 if(officer){box(root,[.31,.08,.3],[0,1.76,0],dark);box(root,[.25,.025,.19],[0,1.72,.16],dark);box(root,[.045,.06,.012],[-.1,1.34,.128],metal);box(root,[.08,.16,.07],[.23,.91,0],dark);}
 const arms=[-1,1].map(side=>{const joint=new THREE.Group();joint.position.set(side*.25,1.4,0);root.add(joint);box(joint,[.13,.28,.15],[0,-.14,0],cloth);const elbow=new THREE.Group();elbow.position.y=-.28;joint.add(elbow);box(elbow,[.11,.26,.12],[0,-.13,0],skin);sphere(elbow,.065,[0,-.29,0],skin);return {joint,elbow};});
 const legs=[-1,1].map(side=>{const joint=new THREE.Group();joint.position.set(side*.11,.88,0);root.add(joint);box(joint,[.16,.4,.19],[0,-.2,0],cloth);const knee=new THREE.Group();knee.position.y=-.4;joint.add(knee);box(knee,[.14,.39,.16],[0,-.195,0],cloth);box(knee,[.17,.09,.29],[0,-.43,.055],dark);return {joint,knee};});
 return {root,arms,legs,materials};
}
function pose(person,{walk=0,time=0,secure=0,surrender=0,seated=0}={}){
 person.legs.forEach(({joint,knee},i)=>{joint.rotation.x=Math.sin(time*8+i*Math.PI)*walk*.48-seated*1.1;knee.rotation.x=Math.max(0,-Math.sin(time*8+i*Math.PI))*walk*.7+seated*1.3;});
 person.arms.forEach(({joint,elbow},i)=>{joint.rotation.x=-Math.sin(time*8+i*Math.PI)*walk*.32-secure*.9; joint.rotation.z=(i?1:-1)*surrender*1.6;elbow.rotation.x=-secure*.8;});
}
function reachArm(arm,target,blend=1){
 const down=new THREE.Vector3(0,-1,0),delta=target.clone().sub(arm.joint.position),d=Math.min(.565,Math.max(.02,delta.length())),direction=delta.normalize();
 const along=(.28*.28-.29*.29+d*d)/(2*d),bend=new THREE.Vector3(0,0,-1).addScaledVector(direction,direction.z).normalize();
 const elbow=arm.joint.position.clone().addScaledVector(direction,along).addScaledVector(bend,Math.sqrt(Math.max(0,.28*.28-along*along)));
 const upper=new THREE.Quaternion().setFromUnitVectors(down,elbow.clone().sub(arm.joint.position).normalize());
 const lower=new THREE.Quaternion().setFromUnitVectors(down,target.clone().sub(elbow).normalize());lower.premultiply(upper.clone().invert());
 arm.joint.quaternion.slerp(upper,blend);arm.elbow.quaternion.slerp(lower,blend);
}
export class PoliceCaptureScene{
 constructor(scene){
  this.group=new THREE.Group();this.group.name='Police capture sequence';this.group.visible=false;scene.add(this.group);
  this.officers=[person(true,0),person(true,1)];this.driver=person(false,2);for(const p of [...this.officers,this.driver])this.group.add(p.root);
  this.doors=[-1,1].map(side=>{const root=new THREE.Group();root.name=`Patrol exit door ${side}`;const paint=new THREE.MeshStandardMaterial({color:'#d7dedc',metalness:.55,roughness:.26}),glass=new THREE.MeshStandardMaterial({color:'#152b35',metalness:.2,roughness:.13});
   for(const [size,y,mat]of [[[1.35,.46,.045],.64,paint],[[1.25,.23,.025],.99,glass]]){const mesh=new THREE.Mesh(new THREE.BoxGeometry(...size),mat);mesh.position.set(-.675,y,0);mesh.castShadow=true;root.add(mesh);}this.group.add(root);return {root,side};});
  this.cuffs=new THREE.Group();this.cuffs.name='Visible secured wrists';const metal=new THREE.MeshStandardMaterial({color:'#c5d1d5',metalness:.9,roughness:.23});for(const x of [-.08,.08]){const ring=new THREE.Mesh(new THREE.TorusGeometry(.055,.014,6,12),metal);ring.position.x=x;this.cuffs.add(ring);}const link=new THREE.Mesh(new THREE.BoxGeometry(.11,.022,.022),metal);this.cuffs.add(link);this.driver.root.add(this.cuffs);
 }
 update(model,{menu=false}={}){
  const c=model.capture;this.group.visible=!menu&&!!c&&['capturing','busted'].includes(model.state);if(!this.group.visible)return;
  const t=c.elapsed,exit=captureEase(t/1.4),approach=captureEase((t-1.4)/3.4),secure=captureEase((t-5.2)/1.4);
  this.doors.forEach(({root,side})=>{const co=Math.cos(c.cop.heading),si=Math.sin(c.cop.heading);root.position.set(c.cop.x+co*.7-si*side*.94,c.cop.y,c.cop.z+si*.7+co*side*.94);root.rotation.y=-c.cop.heading+side*captureEase(t/.5)*(1-captureEase((t-1.2)/.6))*1.15;root.visible=t<1.8;});
  this.officers.forEach((officer,i)=>{const track=c.officers[i],point=t<1.4?{x:mix(track.start.x,track.path[0].x,exit),y:mix(track.start.y,track.path[0].y,exit),z:mix(track.start.z,track.path[0].z,exit),heading:-c.cop.heading+(track.door>0?0:Math.PI)}:sampleCapturePath(track.path,approach);
   officer.root.position.set(point.x,point.y-(1-exit)*.35,point.z);officer.root.rotation.y=t<4.8?point.heading:Math.atan2(c.suspect.x-point.x,c.suspect.z-point.z);officer.root.visible=t>.15;
   pose(officer,{walk:t>1.4&&t<4.8?1:0,time:t,secure:i===0?secure:secure*.4,seated:1-exit});
  });
  const out=captureEase((t-3.3)/1.1),from=c.player,driver=this.driver;
  driver.root.visible=t>3.3;driver.root.position.set(mix(from.x,c.suspect.x,out),mix(from.y-.45,c.suspect.y,out),mix(from.z,c.suspect.z,out));
  driver.root.rotation.y=-c.player.heading+(c.side>0?Math.PI:0);
  pose(driver,{seated:1-out,surrender:out*(1-secure),secure:0});
  // Lower the driver's hands behind their back while the first officer reaches in.
  driver.arms.forEach((arm,i)=>reachArm(arm,new THREE.Vector3(i?.08:-.08,.99,-.27),secure));
  this.cuffs.visible=t>=6.35;this.cuffs.position.set(0,.99,-.27);
  this.group.updateMatrixWorld(true);
  const wrist=driver.root.localToWorld(new THREE.Vector3(0,.99,-.27));
  const arresting=this.officers[0];const target=arresting.root.worldToLocal(wrist.clone());reachArm(arresting.arms[0],target,secure);reachArm(arresting.arms[1],target,secure);
 }
 camera(c,aspect=1){
  if(c.elapsed>=4.8){const h=c.player.heading,scale=Math.max(1,.65/aspect),p=c.suspect;return {position:[p.x+(Math.cos(h)*5-Math.sin(h)*c.side*3.5)*scale,p.y+2.7*scale,p.z+(Math.sin(h)*5+Math.cos(h)*c.side*3.5)*scale],target:[p.x,p.y+1.05,p.z],fov:53};}
  const x=(c.player.x+c.cop.x)/2,z=(c.player.z+c.cop.z)/2,y=Math.max(c.player.y,c.cop.y),h=c.player.heading,scale=Math.max(1,.95/aspect);
  return {position:[x+(-Math.cos(h)*6-Math.sin(h)*c.side*10)*scale,y+5*scale,z+(-Math.sin(h)*6+Math.cos(h)*c.side*10)*scale],target:[x,y+.8,z],fov:53};
 }
 dispose(){const geometries=new Set(),materials=new Set();this.group.traverse(o=>{if(o.isMesh){geometries.add(o.geometry);materials.add(o.material);}});for(const g of geometries)g.dispose();for(const m of materials)m.dispose();this.group.removeFromParent();}
}
