/** Original V17 R3 menu pavilion: real geometry, original in-game palms, no reference-image pixels. */
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { Reflector } from './showroom-reflector.js';

const mat=(name,color,roughness=.5,metalness=0)=>new THREE.MeshStandardMaterial({name,color,roughness,metalness,fog:false});
const SUN=new THREE.Vector3(-.20,.085,-1).normalize();
function sunsetSky(){
 return new THREE.Mesh(new THREE.SphereGeometry(5000,48,24),new THREE.ShaderMaterial({name:'Showroom sunset sky',side:THREE.BackSide,depthWrite:true,fog:false,uniforms:{sunDirection:{value:SUN}},vertexShader:'varying vec3 direction;void main(){direction=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:`
 varying vec3 direction;uniform vec3 sunDirection;
 float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.)),f.x),f.y);}
 void main(){vec3 d=normalize(direction);float h=max(0.,d.y);float glow=pow(max(0.,dot(d,sunDirection)),12.);vec3 horizon=vec3(.63,.24,.085),top=vec3(.07,.12,.19);vec3 c=mix(horizon,top,pow(smoothstep(0.,.70,h),.55));c=mix(c,vec3(.95,.52,.18),glow*.70);vec2 p=d.xz/(max(.035,d.y)+.22)*3.3;float cloud=noise(p)+.55*noise(p*2.1)+.24*noise(p*4.3);float cloudMask=smoothstep(.86,1.22,cloud)*smoothstep(.025,.12,h)*(1.-smoothstep(.55,.9,h));c=mix(c,mix(vec3(.105,.13,.17),vec3(.80,.37,.16),glow),cloudMask*.64);float disc=smoothstep(.99980,.99994,dot(d,sunDirection));c+=vec3(1.,.60,.22)*disc*6.;if(d.y<0.)c=mix(horizon,vec3(.035,.07,.08),min(1.,-d.y*7.));gl_FragColor=vec4(c,1.);
#include <tonemapping_fragment>
#include <colorspace_fragment>}`.replace('//#','\n#').replace(';#include',';\n#include')}));
}
const floorShader={
 name:'R3 dark honed slate with actual planar reflection',
 uniforms:{color:{value:null},tDiffuse:{value:null},textureMatrix:{value:null}},
 vertexShader:'uniform mat4 textureMatrix;varying vec4 reflectionUV;varying vec2 floorPosition;void main(){reflectionUV=textureMatrix*vec4(position,1.);floorPosition=position.xy;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
 fragmentShader:`uniform sampler2D tDiffuse;uniform vec3 color;varying vec4 reflectionUV;varying vec2 floorPosition;
 void main(){vec2 uv=reflectionUV.xy/reflectionUV.w;vec3 r=texture2D(tDiffuse,uv).rgb*.4;r+=(texture2D(tDiffuse,uv+vec2(.0015,0.)).rgb+texture2D(tDiffuse,uv-vec2(.0015,0.)).rgb+texture2D(tDiffuse,uv+vec2(0.,.0015)).rgb+texture2D(tDiffuse,uv-vec2(0.,.0015)).rgb)*.15;vec2 tile=floorPosition/1.65;vec2 grid=abs(fract(tile-.5)-.5)/max(fwidth(tile),vec2(.001));float seam=1.-min(min(grid.x,grid.y),1.);float variation=fract(sin(dot(floor(tile),vec2(73.1,161.7)))*17713.1);float grain=sin(floorPosition.x*4.7+sin(floorPosition.y*3.))*sin(floorPosition.y*1.8)*.013;vec3 c=mix(color*(.82+variation*.16+grain),r,.70);c*=1.-seam*.18;gl_FragColor=vec4(c,1.);\n#include <tonemapping_fragment>\n#include <colorspace_fragment>}`
};

export function createCoastalShowroom(models={}){
 const group=new THREE.Group();group.name='V17 R3 Sunset coastal glass pavilion';group.position.set(10000,0,10000);group.visible=false;
 const steel=mat('Powder-coated charcoal steel','#10161b',.29,.7),wood=mat('Warm cedar ceiling','#623217',.46),slatEdge=mat('Cedar slat seams','#3e2b20',.72),stone=mat('Terrace stone','#66594b',.65),cabinet=mat('Walnut workshop cabinetry','#50301c',.38),dark=mat('Workshop dark details','#1d282d',.42,.3),pot=mat('Warm ceramic planters','#a99e89',.7),leaves=mat('Potted palm leaves','#3d5030',.8);
 const light=new THREE.MeshBasicMaterial({name:'Warm architectural light strips',color:new THREE.Color('#ffe3b0').multiplyScalar(5),toneMapped:true,fog:false});
 const batches=new Map();
 function box(w,h,d,x,y,z,m,rz=0){let g=new THREE.BoxGeometry(w,h,d);if(rz)g.rotateZ(rz);g.translate(x,y,z);if(!batches.has(m))batches.set(m,[]);batches.get(m).push(g);}
 function beam(a,b,width,material){const d=new THREE.Vector3().subVectors(b,a),g=new THREE.BoxGeometry(width,d.length(),width),q=new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize());g.applyQuaternion(q);g.translate(...a.clone().add(b).multiplyScalar(.5));if(!batches.has(material))batches.set(material,[]);batches.get(material).push(g);}
 // The pavilion extends behind the UI/camera; no raised platform or tabletop.
 const floor=new Reflector(new THREE.PlaneGeometry(70,70),{color:'#222a30',textureWidth:512,textureHeight:512,multisample:0,clipBias:.003,shader:floorShader});floor.name='Actual reflected car and glazing floor';floor.rotation.x=-Math.PI/2;floor.position.set(5,-.012,5);floor.material.fog=false;group.add(floor);
 box(42,.14,38,4,6.45,4,wood);
 for(let z=-15;z<24;z+=.24)box(42,.018,.012,4,6.365,z,slatEdge);
 for(const x of [-13,-6,1,8,15,22]){box(.16,6.5,.16,x,3.24,-9,steel);box(.2,.24,38,x,6.25,4,steel);box(.035,.025,36,x+.15,6.10,4,light);}
 for(const z of [-9,-2,5,12,19]){box(.18,6.5,.18,-13,3.24,z,steel);box(42,.2,.18,4,6.25,z,steel);}
 for(const y of [.18,2.8,6.15]){box(35,.085,.10,4.5,y,-9,steel);box(.10,.085,28,-13,y,5,steel);}
 beam(new THREE.Vector3(-12.8,.12,-8.9),new THREE.Vector3(-6.2,6.1,-8.9),.10,steel);
 const glass=new THREE.MeshPhysicalMaterial({name:'Clear coastal glazing',color:'#b5c2c9',metalness:.15,roughness:.08,transparent:true,opacity:.035,depthWrite:false,side:THREE.DoubleSide,fog:false});
 const window=new THREE.Mesh(new THREE.PlaneGeometry(35,6),glass);window.position.set(4.5,3.05,-9.03);group.add(window);
 box(70,.16,6,5,-.15,-12,stone);box(70,.12,1,5,-.09,-9.65,dark);
 // Quiet workshop furniture on the far left, matching the reference's low sideboard.
 box(6.8,1.28,1.0,-8.9,.64,-7.8,cabinet);box(7.0,.12,1.15,-8.9,1.34,-7.8,dark);box(6.7,.025,.025,-8.9,1.26,-7.26,light);
 for(let x=-11.9;x<-5.6;x+=1.1){box(.025,1.13,.025,x,.65,-7.285,dark);box(.2,.025,.05,x+.45,.97,-7.22,steel);}
 // Leaning coastal-map frame is physical scenery; no private screenshot art is embedded.
 box(1.25,1.9,.10,-7.8,2.34,-8.05,dark);box(1.1,1.73,.012,-7.8,2.34,-7.99,stone);
 for(let i=0;i<9;i++){const x=-8.15+i*.078,y=3.02-i*.16;box(.035,.20,.015,x,y,-7.98,dark,.32);}
 for(const [x,z,s] of [[-4.8,-7.3,.9],[9.7,-8,.8],[-12.1,1.3,1.1]]){
  const p=new THREE.Mesh(new THREE.CylinderGeometry(.34,.23,.63,16),pot);p.position.set(x,.315,z);group.add(p);
  const source=models['CoconutPalm_B.glb']||models['CoconutPalm_A.glb'];if(source){const plant=source.clone(true);plant.scale.setScalar(.18*s);plant.position.set(x,.5,z);plant.traverse(o=>{if(o.isMesh){o.material=Array.isArray(o.material)?o.material.map(m=>{const c=m.clone();c.fog=false;return c;}):o.material.clone();if(!Array.isArray(o.material))o.material.fog=false;}});group.add(plant);}
 }
 // Actual loaded, original palms live outside the glass, not on a photographic plane.
 const palmPlacements=[[-13,-19,.90,1.1],[-3,-18,1.05,.4],[2,-20,1.15,-.5],[8,-17,.96,2.2],[15,-23,1.24,1.7],[24,-25,1.1,.2]];
 for(const [i,[x,z,s,yaw]] of palmPlacements.entries()){const source=models[i%2?'CoconutPalm_B.glb':'CoconutPalm_A.glb']||models['CoconutPalm_A.glb']||models['CoconutPalm_B.glb'];if(!source)continue;const palm=source.clone(true);palm.position.set(x,-.3,z);palm.rotation.y=yaw;palm.scale.setScalar(s);palm.traverse(o=>{if(o.isMesh){o.castShadow=false;o.receiveShadow=false;o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();for(const m of Array.isArray(o.material)?o.material:[o.material]){m.fog=false;m.envMapIntensity=.22;if(/leaf|frond/i.test(m.name))m.color.multiplyScalar(.58);}}});group.add(palm);}
 // Filtered wave normals and view-dependent warm sun streak, not a flat turquoise plane.
 const ocean=new THREE.Mesh(new THREE.PlaneGeometry(10000,10000,1,1),new THREE.ShaderMaterial({name:'R3 sunset ocean',fog:false,uniforms:{time:{value:0},sunDirection:{value:SUN}},vertexShader:'varying vec3 waterPosition;varying vec3 worldPosition;void main(){waterPosition=position;worldPosition=(modelMatrix*vec4(position,1.)).xyz;gl_Position=projectionMatrix*viewMatrix*vec4(worldPosition,1.);}',fragmentShader:`varying vec3 waterPosition;varying vec3 worldPosition;uniform float time;uniform vec3 sunDirection;
 void main(){vec2 p=waterPosition.xy;float band=sin(p.y*.72+sin(p.x*.18)+time*.28);float fine=sin(p.y*3.8+p.x*.31-time*.4);float attenuation=1.-smoothstep(.6,2.5,length(fwidth(p)));vec3 n=normalize(vec3(sin(p.x*.26+p.y*.11)*.035,1.,band*.065+fine*.025*attenuation));vec3 view=normalize(cameraPosition-worldPosition);float fresnel=pow(1.-max(0.,dot(n,view)),4.);float glint=pow(max(0.,dot(reflect(-sunDirection,n),view)),180.);float halo=pow(max(0.,dot(reflect(-sunDirection,vec3(0.,1.,0.)),view)),12.);vec3 c=mix(vec3(.012,.042,.055),vec3(.12,.17,.18),fresnel);c+=vec3(.14,.065,.02)*halo+vec3(2.4,1.02,.25)*glint;c*=.92+band*.08;gl_FragColor=vec4(c,1.);
#include <tonemapping_fragment>
#include <colorspace_fragment>}`}));ocean.rotation.x=-Math.PI/2;ocean.position.set(0,-.52,0);group.add(ocean);
 // Far headlands are low, broad original silhouettes, not mountain-shaped foreground props.
 const islandMaterial=mat('Hazy distant headlands','#364f57',1);islandMaterial.emissive.set('#50656c');islandMaterial.emissiveIntensity=.7;
 for(const [x,z,s] of [[-180,-620,1],[-80,-680,.7],[210,-700,.8],[330,-770,1.1]]){const mound=new THREE.Mesh(new THREE.SphereGeometry(1,16,8),islandMaterial);mound.scale.set(80*s,4*s,25*s);mound.position.set(x,-1,z);group.add(mound);}
 // Original curved foliage meshes: no billboard, photograph or private reference texture.
 const borderMaterials=[mat('Sunset border deep leaves','#19291e',.78),mat('Sunset border lit leaves','#394024',.72)];
 const borderGeometries=[[],[]];
 for(let i=0;i<42;i++){const x=-22+i*1.15,z=-13.1-Math.sin(i*2.17)*1.0;for(let j=0;j<7;j++){const angle=j*Math.PI*2/7+i*.87,len=.8+((i*7+j*3)%11)/16;const vertices=[],indices=[];for(let k=0;k<=10;k++){const t=k/10,r=t*len,y=.12+Math.sin(t*Math.PI*.75)*len*.74,width=Math.sin(t*Math.PI)*len*.11;for(const side of [-1,1])vertices.push(x+Math.cos(angle)*r+Math.sin(angle)*width*side,y,z+Math.sin(angle)*r-Math.cos(angle)*width*side);if(k<10){let a=k*2;indices.push(a,a+1,a+2,a+1,a+3,a+2);}}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setIndex(indices);g.computeVertexNormals();borderGeometries[(i+j)%2].push(g);}}
 for(let i=0;i<2;i++){borderMaterials[i].side=THREE.DoubleSide;const mesh=new THREE.Mesh(mergeGeometries(borderGeometries[i],false),borderMaterials[i]);mesh.name='Original planted coastal border';group.add(mesh);borderGeometries[i].forEach(g=>g.dispose());}
 const sky=sunsetSky();sky.renderOrder=-900;group.add(sky);
 for(const [material,geometries] of batches){const mesh=new THREE.Mesh(mergeGeometries(geometries,false),material);mesh.name=material.name;mesh.castShadow=material!==light;mesh.receiveShadow=true;group.add(mesh);geometries.forEach(g=>g.dispose());}
 const lights=new THREE.Group();lights.name='Menu-only sunset studio lighting';lights.position.copy(group.position);lights.visible=false;
 const key=new THREE.PointLight('#ffbe7b',125,32,2);key.position.set(-1,5,2);const fill=new THREE.PointLight('#9bb4cd',45,25,2);fill.position.set(4,3,5);const rim=new THREE.DirectionalLight('#ffb466',1.65);rim.position.copy(SUN).multiplyScalar(40);rim.target.position.set(0,0,0);lights.add(key,fill,rim,rim.target);

 return {group,lights,floor,update(time){ocean.material.uniforms.time.value=time;},dispose(){floor.dispose();}};
}

/** Menu-only HDR reflection rig. The gameplay environment is never modified. */
export function createShowroomReflectionScene(){
 const scene=new THREE.Scene();scene.name='R3 original warm coastal reflection rig';scene.background=new THREE.Color('#101923');
 const sky=sunsetSky();sky.scale.setScalar(.1);scene.add(sky);
 const panel=(name,w,h,x,y,z,color,intensity,rx=0,ry=0)=>{const m=new THREE.MeshBasicMaterial({name,color:new THREE.Color(color).multiplyScalar(intensity),side:THREE.DoubleSide,toneMapped:false});const o=new THREE.Mesh(new THREE.PlaneGeometry(w,h),m);o.position.set(x,y,z);o.rotation.set(rx,ry,0);scene.add(o);};
 panel('Dark cedar reflection ceiling',38,32,0,6.3,0,'#2c170d',1,Math.PI/2);
 panel('Long warm ceiling reflection',19,.24,0,5.9,-2,'#ffe5b6',8,Math.PI/2);
 panel('Long cool softbox reflection',15,1.2,2,5.8,4,'#b9d7ed',2.2,Math.PI/2);
 panel('Warm window reflection',24,4,0,2.7,-12,'#f8ad61',.7);
 return scene;
}
