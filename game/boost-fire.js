import * as THREE from 'three';

// Original arcade exhaust effect, NOT a representation of Tesla cold-gas flight.
// Both nozzles and crossed flame carrier meshes are authored in Blender. Their
// UVs drive procedural colour/opacity here; there are no photographic textures.
export const BOOST_FIRE_MOUNTS=Object.freeze([[-2.30,.26,-.56],[-2.30,.26,.56]].map(Object.freeze));
export const BOOST_FIRE_COLORS=Object.freeze({regular:['#ff5308','#ffce36','#fff5c4'],ultra:['#7120ff','#d554ff','#f4dcff']});
const VERTEX=`varying vec2 flameUV;
void main(){flameUV=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`;
const FRAGMENT=`varying vec2 flameUV;
uniform float flameTime;uniform float strength;uniform float seed;
uniform vec3 outerColor;uniform vec3 innerColor;uniform vec3 coreColor;
float noiseF(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
 float a=fract(sin(dot(i,vec2(127.1,311.7)))*43758.5453);
 float b=fract(sin(dot(i+vec2(1.,0.),vec2(127.1,311.7)))*43758.5453);
 float c=fract(sin(dot(i+vec2(0.,1.),vec2(127.1,311.7)))*43758.5453);
 float d=fract(sin(dot(i+vec2(1.,1.),vec2(127.1,311.7)))*43758.5453);
 return mix(mix(a,b,f.x),mix(c,d,f.x),f.y);}
void main(){
 float u=clamp(flameUV.x,0.,1.),v=flameUV.y*2.-1.;
 float flow=noiseF(vec2(u*8.-flameTime*10.,v*3.+seed));
 float fine=noiseF(vec2(u*21.-flameTime*17.,v*7.-seed));
 float bend=sin(u*17.-flameTime*22.+seed)*u*.13;
 float density=max(0.,1.-abs(v+bend)/(1.-u*.62));
 float edge=smoothstep(.02,.23,density+(flow-.5)*.24);
 float root=smoothstep(0.,.035,u),tail=1.-smoothstep(.55+.10*flow,1.,u);
 float alpha=edge*root*tail*(.48+.34*flow+.18*fine)*strength;
 if(alpha<.008)discard;
 float hot=clamp(density*(1.-u*.7),0.,1.);
 vec3 color=mix(outerColor,innerColor,smoothstep(.18,.65,hot));
 color=mix(color,coreColor,smoothstep(.65,.96,hot)*.85);
 gl_FragColor=vec4(color*(.86+.30*fine),alpha);
 #include <colorspace_fragment>
}`;

export class ArcadeBoostFire{
 constructor(parent,template){
  if(!template?.isObject3D)throw new Error('Blender-authored ArcadeBoostNozzle.glb is required.');
  this.parent=parent;this.group=new THREE.Group();this.group.name='ArcadeBoostFire';parent.add(this.group);
  this.strength=0;this.mode='regular';this.clock=0;this.disposed=false;this.emitters=[];this.materials=new Set();
  BOOST_FIRE_MOUNTS.forEach((position,index)=>{
   const mount=template.clone(true);mount.name=`ArcadeBoostMount_${index}`;mount.position.fromArray(position);mount.rotation.z=Math.PI/60;this.group.add(mount);
   const colors=BOOST_FIRE_COLORS.regular;
   const material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,depthTest:true,side:THREE.DoubleSide,blending:THREE.AdditiveBlending,toneMapped:false,
    uniforms:{flameTime:{value:0},strength:{value:0},seed:{value:index*8.31+1.7},outerColor:{value:new THREE.Color(colors[0])},innerColor:{value:new THREE.Color(colors[1])},coreColor:{value:new THREE.Color(colors[2])}},vertexShader:VERTEX,fragmentShader:FRAGMENT});
   this.materials.add(material);const flames=[];
   mount.traverse(o=>{if(!o.isMesh)return;if(o.name.startsWith('FlameCards')){o.material=material;o.visible=false;o.renderOrder=4;flames.push(o);}else{o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();for(const m of Array.isArray(o.material)?o.material:[o.material])this.materials.add(m);o.castShadow=false;o.receiveShadow=true;}});
   if(!flames.length)throw new Error('Boost nozzle is missing its Blender FlameCards mesh.');
   this.emitters.push({mount,material,flames});
  });
  this.light=new THREE.PointLight(BOOST_FIRE_COLORS.regular[0],0,4.5,2);this.light.position.set(-2.34,.28,0);this.light.castShadow=false;this.group.add(this.light);
 }
 update(state,dt,{paused=false,menu=false,active=true,time}={}){
  if(this.disposed)return;
  const stopped=paused||menu||!active;
  const requested=!stopped&&!!(state?.boosting||state?.ultraBoosting);
  const step=Number.isFinite(dt)?Math.max(0,Math.min(.1,dt)):0;
  if(stopped)this.strength=0;
  else this.strength+=(Number(requested)-this.strength)*(1-Math.exp(-step*(requested?28:25)));
  if(this.strength<.001)this.strength=0;
  if(!paused)this.clock=Number.isFinite(time)?time:this.clock+step;
  if(requested)this.mode=state.ultraBoosting?'ultra':'regular';
  const colors=BOOST_FIRE_COLORS[this.mode],ultra=this.mode==='ultra',speed=Math.min(1,Math.abs(state?.speed||0)/90);
  const pulse=.94+.06*Math.sin(this.clock*37),length=(ultra?1.45+.30*speed:.72+.24*speed)*pulse;
  for(const emitter of this.emitters){const u=emitter.material.uniforms;u.flameTime.value=this.clock;u.strength.value=this.strength;u.outerColor.value.set(colors[0]);u.innerColor.value.set(colors[1]);u.coreColor.value.set(colors[2]);for(const flame of emitter.flames){flame.visible=this.strength>.008;flame.scale.set(length,ultra?1.13:1,ultra?1.13:1);flame.position.x=.08*(length-1);}}
  this.light.color.set(colors[0]);this.light.intensity=(ultra?4.4:2.2)*this.strength;
 }
 reset(){this.update({},0,{active:false});}
 dispose(){if(this.disposed)return;this.disposed=true;this.group.removeFromParent();for(const material of this.materials)material.dispose();this.materials.clear();this.emitters.length=0;this.light.intensity=0;}
}
