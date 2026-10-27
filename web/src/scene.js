import {DrivingCameraFilter} from './driving-camera.js';
import {SimReadyPilot} from './simready-pilot.js';
import {RoadLighting} from './road-lighting.js';
import * as THREE from 'three';
import { createCoastalShowroom,createShowroomReflectionScene } from './showroom-scene.js';
import {renderPixelRatio,RENDER_RESOLUTIONS,configureOpaqueSky} from './render-metrics.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { ScenicTransit } from './transit.js';
import { AirTrafficRenderer } from './air-traffic.js';
import { SurfaceCameraRig,surfaceQuaternion } from './surface-camera.js';
import { makeAtmosphere,RacingPresentation } from './finish-fx.js';
import { NearDetailField } from './detail-lod.js';
import { ArcadeBoostFire } from './boost-fire.js';
import { RaceCollectibles } from './collectibles.js';
import { CAR_CATALOG } from './garage.js';
import {validCinematicPose} from './cinematic-camera.js';
import {PoliceCaptureScene} from './police-capture-scene.js';
import {refineCarPaint,refineFacade} from './capture-materials.js';
import {installUpgradeVisuals,applyUpgradeVisuals} from './upgrade-visuals.js';
import {applyRoadMicroSurface,makeCoastalReflectionScene} from './surface-materials.js';
import { buildTeaPlacementIndex,selectTeaDetailPlacements } from './tea-placement.js';
const BASE=new URL('./public/assets/',document.baseURI);
const assetURL=name=>window.__MALABAR_ASSETS__?.[name]||new URL(name,BASE).href;
const materialList=m=>Array.isArray(m)?m:[m];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export const normalizeWorldData=data=>({...data,...(data.world||{})});
const SHADOW_FLOOR_ROTATION=new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI/2,0,0));
// A surface normal is independent of the car's yaw. Project its forward axis
// onto that plane so a sideways car/shadow still rests on the same ramp.
function groundOrientation(state){
 const surface=surfaceQuaternion(state.surfaceFrame);if(surface)return surface;
 const slope=state.groundPitch??state.roadPitch??0,h=state.groundHeading??state.heading;
 const hasNormal=[state.groundNormalX,state.groundNormalY,state.groundNormalZ].every(Number.isFinite);
 const up=hasNormal?new THREE.Vector3(state.groundNormalX,state.groundNormalY,state.groundNormalZ).normalize():new THREE.Vector3(-Math.sin(slope)*Math.cos(h),Math.cos(slope),-Math.sin(slope)*Math.sin(h));
 const forward=new THREE.Vector3(Math.cos(state.heading),0,Math.sin(state.heading));forward.addScaledVector(up,-forward.dot(up)).normalize();
 const right=new THREE.Vector3().crossVectors(forward,up).normalize();
 return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(forward,up,right));
}
export class CoastRenderer{
 constructor(canvas,{onProgress=()=>{},worldFile='course_runtime.json'}={}){
  this.worldFile=worldFile;this.canvas=canvas;this.onProgress=onProgress;this.scene=new THREE.Scene();this.scene.background=new THREE.Color('#aabec3');this.scene.fog=new THREE.FogExp2('#bac2bc',.00145);
  this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,powerPreference:'high-performance'});
  this.resolutionMode='auto';this.resolutionRevision=0;this.actualAntialias=!!this.renderer.getContext().getContextAttributes()?.antialias;
  this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.05;
  this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  this.camera=new THREE.PerspectiveCamera(63,1,.12,6500);this.quality=matchMedia('(pointer:coarse)').matches?'balanced':'high';this.renderer.shadowMap.enabled=this.quality==='high';
  this.reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;this.clock=0;this.worldTime=0;this.transit=[];this.dynamicObstacles=[];this.cars=[];this.environmentChunks=[];this.waterShaders=[];this.windShaders=[];this.windowMaterials=[];this.orbitYaw=0;this.orbitPitch=.12;this.cameraMode=0;this.cameraReset=true;
  this.hemisphere=new THREE.HemisphereLight('#e7f0ef','#485438',2.0);this.scene.add(this.hemisphere);
  this.sun=new THREE.DirectionalLight('#ffddb1',3.1);this.sun.position.set(70,90,-30);this.sun.castShadow=true;
  const sc=this.sun.shadow.camera;sc.left=-48;sc.right=48;sc.top=48;sc.bottom=-48;sc.near=1;sc.far=240;
  this.sun.shadow.mapSize.set(2048,2048);this.sun.shadow.bias=-.0004;this.sun.shadow.normalBias=.06;this.scene.add(this.sun,this.sun.target);
  const pmrem=new THREE.PMREMGenerator(this.renderer),menuReflection=createShowroomReflectionScene();this.showroomEnvironment=pmrem.fromScene(menuReflection,.025,.1,1000).texture;menuReflection.traverse(o=>{if(o.isMesh){o.geometry.dispose();o.material.dispose();}});const coastal=makeCoastalReflectionScene();this.coastalEnvironment=pmrem.fromScene(coastal,.025).texture;coastal.traverse(o=>{if(o.isMesh){o.geometry.dispose();o.material.dispose();}});this.scene.environment=this.coastalEnvironment;pmrem.dispose();
  this.sky=configureOpaqueSky(makeAtmosphere());this.scene.add(this.sky);
  this.resize();
 }
 async load(){
  const manager=new THREE.LoadingManager();manager.onProgress=(_,n,total)=>this.onProgress(n/total,`Preparing ${this.worldFile?.includes('highlands')?'highlands':'coast'}  ${n} / ${total}`);
  const loader=new GLTFLoader(manager);this.loader=loader;
  const worldData=await(await fetch(assetURL(this.worldFile||'course_runtime.json'))).json();this.world=normalizeWorldData(worldData);
  if(this.world.terrain_grid_file)this.world.terrain_grid=await(await fetch(assetURL(this.world.terrain_grid_file))).json();
  this.carInfo=await(await fetch(assetURL('car_manifest.json'))).json();
  this.furniture=(await(await fetch(assetURL(this.world.furniture_file||'furniture_colliders.json'))).json()).colliders;
  this.infrastructureColliders=this.world.collision_file?(await(await fetch(assetURL(this.world.collision_file))).json()).colliders||[]:[];
  this.route=(this.world.route_points||this.world.route_points_m||[]).map(p=>Array.isArray(p)?{x:p[0],y:p[1],z:p[2]}:p);
  if(this.route.length<100)throw new Error('Smoothed route data is missing. Rebuild web environment assets.');
  this.detailFields=[];this.detailStats={enabled:false,instances:0,triangles:0,draws:0,teaRadius:0,treeRadius:0};
  const hasHighlandDetail=this.world.id==='highlands';
  if(hasHighlandDetail)this.teaDetail=await(await fetch(assetURL('tea_detail_rows.json'))).json();
  const propNames=[...new Set(this.world.prop_instances.map(p=>p.asset))];const hasCanalDetail=propNames.includes('CanalRainTree');
  const files=[...new Set([...(this.worldFile==='course_runtime.json'?['SimReadyFenceNear.glb','SimReadyFenceFar.glb','SimReadyCrateNear.glb','SimReadyCrateFar.glb']:[]),...this.world.course_meshes.map(p=>p.file),...propNames.map(n=>n+'.glb'),...Object.values(CAR_CATALOG).map(c=>c.asset),'CaptureOfficerNear.glb','CaptureOfficerMobile.glb','CaptureDriverNear.glb','CaptureDriverMobile.glb','police_lightbar.glb','CheckpointGate.glb','ServiceShowroomLoft.glb','CoconutPalm_A.glb','CoconutPalm_B.glb','ArcadeBoostNozzle.glb','ArcadeCoin.glb',...(hasCanalDetail?['CanalRainTreeFar.glb']:[]),...(hasHighlandDetail?['HighlandShadeTreeNear.glb','TeaLeafCluster.glb']:[]),...(this.world.transit_routes||[]).map(r=>r.asset+'.glb'),...(this.world.air_traffic?['helicopter_civilian.glb','helicopter_police.glb','helicopter_rotor_blur.glb']:[])])];
  const loads=await Promise.all(files.map(async file=>[file,(await loader.loadAsync(assetURL(file))).scene]));
  this.models=Object.fromEntries(loads);if(this.worldFile==='course_runtime.json')this.simReadyPilot=new SimReadyPilot(this);
  for(const entry of this.world.course_meshes){
   const group=this.models[entry.file];group.traverse(o=>{if(o.isMesh){o.receiveShadow=true;o.castShadow=/Road|Furniture/.test(entry.file);for(const m of materialList(o.material))this.styleMaterial(m,true);applyRoadMicroSurface(o);}});this.scene.add(group);
  }
  if(!this.world.surface_profile)this.roadLighting=new RoadLighting(this,{center:{x:0,z:0}});
  // Per-material, spatially chunked instancing keeps a 4.5km coast affordable on mobile.
  const buckets=new Map();
  for(const p of this.world.prop_instances){const key=`${p.asset}|${Math.floor(p.position[0]/160)}|${Math.floor(p.position[2]/160)}`;if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(p);}
  const temp=new THREE.Object3D();
  for(const placements of buckets.values()){
   const name=placements[0].asset;const model=this.models[name==='CanalRainTree'&&hasCanalDetail?'CanalRainTreeFar.glb':name+'.glb'];model.updateMatrixWorld(true);
   const group=new THREE.Group();const center=new THREE.Vector3();placements.forEach(p=>center.add(new THREE.Vector3(...p.position)));center.multiplyScalar(1/placements.length);
   model.traverse(o=>{if(!o.isMesh)return;for(const m of materialList(o.material))this.styleMaterial(m,false);
    const tintKind=!Array.isArray(o.material)&&/Warm_Lime_Plaster/.test(o.material.name)?'facade_color':!Array.isArray(o.material)&&/Kerala_Teal_Trim/.test(o.material.name)?'accent_color':null;const material=tintKind?o.material.clone():o.material;const originalColor=tintKind?o.material.color.clone():null;if(tintKind)material.color.set('#ffffff');
    const im=new THREE.InstancedMesh(o.geometry,material,placements.length);im.castShadow=!name.includes('Grass');im.receiveShadow=true;
    placements.forEach((p,i)=>{temp.position.set(...p.position);temp.rotation.set(0,p.yaw_rad,0);temp.scale.setScalar(p.scale);temp.updateMatrix();im.setMatrixAt(i,temp.matrix.clone().multiply(o.matrixWorld));if(tintKind)im.setColorAt(i,p[tintKind]?new THREE.Color(p[tintKind]):originalColor);});
    im.instanceMatrix.needsUpdate=true;if(im.instanceColor)im.instanceColor.needsUpdate=true;im.computeBoundingSphere();group.add(im);
   });group.userData.center=center;this.environmentChunks.push(group);this.scene.add(group);
  }
  const materials=model=>{const a=[];model.traverse(o=>{if(o.isMesh)a.push(...materialList(o.material));});return a;};
  if(hasCanalDetail)this.detailFields.push(new NearDetailField({name:'trees',model:this.models['CanalRainTree.glb'],placements:this.world.prop_instances.filter(p=>p.asset==='CanalRainTree'),scene:this.scene,styleMaterial:m=>this.styleMaterial(m),farMaterials:materials(this.models['CanalRainTreeFar.glb']),high:{radius:80,budget:12,padding:18,fade:16},balanced:{radius:45,budget:6,padding:18,fade:12}}));
  if(hasHighlandDetail){
   this.detailFields.push(new NearDetailField({name:'trees',model:this.models['HighlandShadeTreeNear.glb'],placements:this.world.prop_instances.filter(p=>p.asset==='HighlandShadeTree'),scene:this.scene,styleMaterial:m=>this.styleMaterial(m),farMaterials:materials(this.models['HighlandShadeTree.glb']),high:{radius:95,budget:16,padding:10,fade:18},balanced:{radius:55,budget:6,padding:10,fade:14}}));
   const teaIndex=buildTeaPlacementIndex(this.teaDetail);
   this.detailFields.push(new NearDetailField({name:'tea',model:this.models['TeaLeafCluster.glb'],placements:[],scene:this.scene,styleMaterial:m=>this.styleMaterial(m),farMaterials:materials(this.models['Highlands_Tea.glb']),high:{radius:65,budget:1250,padding:2,fade:12},balanced:{radius:35,budget:500,padding:2,fade:9},selector:(camera,config)=>selectTeaDetailPlacements(this.teaDetail,this.world.terrain_grid,{center:camera.toArray(),radius:config.radius,maxInstances:config.budget,index:teaIndex})}));
  }
  this.showroom=createCoastalShowroom(this.models);this.garageModel=this.showroom.group;this.garageLights=this.showroom.lights;this.scene.add(this.garageModel,this.garageLights);
  this.checkpointMarker=this.models['CheckpointGate.glb'];this.scene.add(this.checkpointMarker);
  this.carTemplate=this.models['car.glb'];this.addCar('#b61920',false);
  ['#f3b83e','#e6e8de','#229ca9'].forEach(c=>this.addCar(c,false));this.addCar('#edf0ee',true);this.addCar('#23394b',true);
  this.waterSurface=[];for(const entry of this.world.course_meshes.filter(e=>/Water/i.test(e.file)))this.models[entry.file].traverse(o=>{if(o.isMesh&&materialList(o.material).some(m=>/ocean|water/i.test(m.name)))this.waterSurface.push(o);});this.scene.updateMatrixWorld(true);this.waterRay=new THREE.Raycaster();
  this.transit=(this.world.transit_routes||[]).map(config=>new ScenicTransit(this.models[config.asset+'.glb'],config,this.scene));
  if(this.world.air_traffic)this.airTraffic=new AirTrafficRenderer(this.scene,{civilian:this.models['helicopter_civilian.glb'],police:this.models['helicopter_police.glb'],blur:this.models['helicopter_rotor_blur.glb']});
  this.makeEffects();this.presentation=new RacingPresentation(this.scene);this.collectibles=new RaceCollectibles(this.scene,this.models['ArcadeCoin.glb']);this.onProgress(1,'Ready. The road is yours.');
 }
 styleMaterial(m,course=false){
  if(m.userData.styled)return;m.userData.styled=true;
  refineFacade(m);
  const n=m.name.toLowerCase();
  m.envMapIntensity=n.includes('glass')?.9:.42;
  if(/deep_window|transit_window|station_glaz|terminal_glaz/.test(n)&&m.emissive){m.emissive.set('#6a786c');m.emissiveIntensity=.015;m.userData.nightIntensity=.4;m.userData.dayIntensity=.015;this.windowMaterials?.push(m);}
  if(/v8_lamp/.test(n)&&m.emissive){m.userData.nightIntensity=1.6;m.userData.dayIntensity=.1;this.windowMaterials?.push(m);}
  if(/leaf|frond|grass/.test(n)){m.side=THREE.DoubleSide;m.roughness=.85;m.color.multiplyScalar(.8);this.windMaterial(m,/grass|tea/.test(n)?.035:n.includes('stem')?.025:.07,/grass|tea/.test(n));}
  if(/asphalt/.test(n)){m.color.set('#343b3c');m.roughness=.94;this.worldGrain(m,28,.20,'asphalt');}
  else if(/sand/.test(n)){m.color.set('#c2a77b');m.roughness=.95;this.worldGrain(m,2,.16);}
  else if(/gravel|shoulder/.test(n)){m.roughness=1;this.worldGrain(m,9,.38,'gravel');}
  else if(/ground/.test(n)){m.color.set('#607448');m.roughness=1;this.worldGrain(m,.16,.42,'landscape');}
  else if(/teacanopy/.test(n)){m.roughness=.95;this.worldGrain(m,1.4,.16);}
  else if(course&&/water|ocean/.test(n)){m.color.set('#297f85');m.roughness=.22;m.metalness=.3;m.envMapIntensity=1.1;this.waterMaterial(m);}
  else if(/foam/.test(n)){m.color.set('#d9e1cb');m.roughness=.8;this.worldGrain(m,1.8,.38);}
  else if(/weatheredwhite/.test(n)){m.color.set('#e5e1cb');m.roughness=.85;}
 }
 windMaterial(m,strength,grass=false){
  m.onBeforeCompile=shader=>{shader.uniforms.windTime={value:0};shader.uniforms.windStrength={value:strength};this.windShaders.push(shader);
   shader.vertexShader='uniform float windTime;uniform float windStrength;\n'+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>\nfloat windPhase=0.;\n#ifdef USE_INSTANCING\nwindPhase=instanceMatrix[3].x*.017+instanceMatrix[3].z*.021;\n#endif\nfloat crown=clamp((position.y-${grass?0:4}.)/${grass?1:5}.,0.,1.);transformed.x+=sin(windTime*.9+windPhase+position.y*.4)*windStrength*crown;transformed.z+=cos(windTime*.7+windPhase+position.x)*windStrength*.6*crown;`);
  };m.customProgramCacheKey=()=>`leafwind-${strength}-${grass}`;m.needsUpdate=true;
 }
 worldGrain(m,scale,amount,kind='grain'){
  m.onBeforeCompile=shader=>{
   shader.uniforms.grainScale={value:scale};shader.uniforms.grainAmount={value:amount};
   shader.vertexShader='varying vec3 vWorldGrain;\n'+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nvec4 grainWorld=vec4(transformed,1.0);\n#ifdef USE_INSTANCING\ngrainWorld=instanceMatrix*grainWorld;\n#endif\nvWorldGrain=(modelMatrix*grainWorld).xyz;');
   shader.fragmentShader='varying vec3 vWorldGrain;uniform float grainScale;uniform float grainAmount;float hashG(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}float noiseG(vec2 p){vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hashG(i),hashG(i+vec2(1,0)),f.x),mix(hashG(i+vec2(0,1)),hashG(i+vec2(1)),f.x),f.y);}\n'+shader.fragmentShader;
   shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\nfloat grain=noiseG(vWorldGrain.xz*grainScale)*.6+noiseG(vWorldGrain.xz*grainScale*13.)*.4;grain=mix(grain,.5,smoothstep(.5,2.,length(fwidth(vWorldGrain.xz*grainScale))));diffuseColor.rgb*=1.+(grain-.5)*grainAmount*2.;');
   if(kind==='asphalt'||kind==='gravel'){shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nroughnessFactor=clamp(roughnessFactor+(grain-.5)*.18,.65,1.);');if(kind==='gravel')shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_begin>','#include <normal_fragment_begin>\nnormal=normalize(normal+vec3(dFdx(grain),dFdy(grain),0.)*.12);');}
   if(kind==='asphalt')shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\ndiffuseColor.rgb*=.92+.16*noiseG(vWorldGrain.xz*.11);');
   if(kind==='landscape')shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\ndiffuseColor.rgb*=mix(vec3(.84,1.02,.78),vec3(1.09,1.02,.88),clamp((vWorldGrain.y-12.)/110.,0.,1.));');
  };m.customProgramCacheKey=()=>`grain-${kind}-${scale}-${amount}`;m.needsUpdate=true;
 }
 waterMaterial(m){
  m.onBeforeCompile=shader=>{shader.uniforms.waterTime={value:0};this.waterShaders.push(shader);
   shader.vertexShader='varying vec3 vWaterPos;\n'+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nvWaterPos=(modelMatrix*vec4(transformed,1.)).xyz;');
   shader.fragmentShader='varying vec3 vWaterPos;uniform float waterTime;\n'+shader.fragmentShader;
   shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_begin>','#include <normal_fragment_begin>\nfloat wx=sin(vWaterPos.x*.43+vWaterPos.z*.17+waterTime*.8)+.45*sin(vWaterPos.x*1.87-vWaterPos.z*.61+waterTime*1.3);float wz=cos(vWaterPos.z*.31-vWaterPos.x*.19-waterTime*.7)+.36*cos(vWaterPos.z*1.31+vWaterPos.x*.71+waterTime);normal=normalize(normal+vec3(wx*.065,wz*.04,sin(vWaterPos.x*.27+vWaterPos.z*.33-waterTime*.4)*.045));');
  };m.customProgramCacheKey=()=>`coastal-water`;m.needsUpdate=true;
 }
 addCar(color,police,variant='red'){
  const brakeLights=[];const group=this.models[CAR_CATALOG[variant]?.asset||'car.glb'].clone(true);group.traverse(o=>{if(o.isMesh){const copy=m=>refineCarPaint(m.clone(),this.carInfo.paint_material);o.material=Array.isArray(o.material)?o.material.map(copy):copy(o.material);o.castShadow=true;o.receiveShadow=true;
   for(const m of materialList(o.material)){if(/LED ruby red|rear red ribbon/.test(m.name)||m.name==='Midnight rear vermilion lights')brakeLights.push(m);m.envMapIntensity=1.25;if(m.name===this.carInfo.paint_material){m.color.set(color);m.metalness=.62;m.roughness=.25;}if(m.name.toLowerCase().includes('glass')){m.roughness=.12;m.metalness=.28;m.color.set('#172b33');}}
  }});
  let bar=null;if(police){bar=this.models['police_lightbar.glb'].clone(true);bar.position.set(0,1.232,0);bar.traverse(o=>{if(o.isMesh)o.material=Array.isArray(o.material)?o.material.map(m=>m.clone()):o.material.clone();});group.add(bar);}
  const steer=this.carInfo.steer_nodes.map(n=>group.getObjectByName(n));const spin=this.carInfo.spin_nodes.map(n=>group.getObjectByName(n));
  const stunt=new THREE.Group();stunt.name='StuntVisual';stunt.position.y=.65;group.add(stunt);group.updateMatrixWorld(true);stunt.attach(group.getObjectByName('CAR_ROOT'));
  const body=group.getObjectByName('CarBody'),wing=group.getObjectByName('AeroWing_Hinge'),fixedWing=group.getObjectByName('RearWing');
  const chassis=new THREE.Group();chassis.name='ChassisVisual';(group.getObjectByName('CAR_ROOT')||group).add(chassis);group.updateMatrixWorld(true);
  for(const part of [body,wing,fixedWing,bar,...['Thruster_Rear_0','Thruster_Rear_1','Thruster_Rear_2','Thruster_Rear_3','Thruster_Down_RL','Thruster_Down_RR'].map(n=>group.getObjectByName(n))])if(part)chassis.attach(part);
  const contactShadow=new THREE.Mesh(new THREE.PlaneGeometry(6.2,3.1),new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{opacity:{value:.42}},vertexShader:'varying vec2 shadowUV;void main(){shadowUV=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',fragmentShader:'varying vec2 shadowUV;uniform float opacity;void main(){vec2 p=(shadowUV-.5)*2.;float a=pow(max(0.,1.-dot(p,p)),1.6)*opacity;gl_FragColor=vec4(0.,0.,0.,a);}'}));contactShadow.rotation.x=-Math.PI/2;contactShadow.renderOrder=2;this.scene.add(contactShadow);
  this.cars.push({group,steer,spin,police,bar,body,chassis,stunt,wing,variant,contactShadow,jets:[],brakeLights,previousSpeed:0});installUpgradeVisuals(this.cars[this.cars.length-1]);applyUpgradeVisuals(this.cars[this.cars.length-1],{});this.scene.add(group);return group;
 }
 isWater(x,z){if(!this.waterRay)return false;this.waterRay.set(new THREE.Vector3(x,30,z),new THREE.Vector3(0,-1,0));return this.waterRay.intersectObjects(this.waterSurface,false).length>0;}
 setPlayerCar(variant){
  if(!Object.hasOwn(CAR_CATALOG,variant)||!this.models[CAR_CATALOG[variant].asset]||this.cars[0]?.variant===variant)return;
  const old=this.cars[0];old.boostFire?.dispose();this.scene.remove(old.group,old.contactShadow);old.contactShadow.geometry.dispose();old.contactShadow.material.dispose();for(const jet of old.jets)jet.mesh.geometry.dispose();old.group.traverse(o=>{if(o.isMesh)materialList(o.material).forEach(m=>m.dispose());});
  this.addCar(CAR_CATALOG[variant].displayColor,false,variant);this.cars[0]=this.cars.pop();this.attachJets(this.cars[0]);this.cameraReset=true;
 }
 attachJets(car){
  car.boostFire=new ArcadeBoostFire(car.chassis,this.models['ArcadeBoostNozzle.glb'],{mounts:CAR_CATALOG[car.variant]?.boostMounts});
  const installed={...car.visualUpgrades};installUpgradeVisuals(car);applyUpgradeVisuals(car,installed);
  const names=car.variant==='silver'?['Thruster_Rear_0','Thruster_Rear_1','Thruster_Rear_2','Thruster_Rear_3','Thruster_Down_RL','Thruster_Down_RR']:[];
  const sockets=names.map(n=>({object:car.group.getObjectByName(n),down:n.includes('Down')})).filter(s=>s.object);
  if(!sockets.length)for(const z of [-.56,.56]){const o=new THREE.Object3D();o.position.set(-2.30,.415,z);car.chassis.add(o);sockets.push({object:o,down:false});const d=new THREE.Object3D();d.name='Fictional_Underbody_FX';d.position.set(-.9,.16,z);car.chassis.add(d);sockets.push({object:d,down:true});}
  for(const socket of sockets){
   const jet=new THREE.Mesh(new THREE.CylinderGeometry(.19,.04,1,12,1,true).translate(0,.5,0),new THREE.MeshBasicMaterial({color:'#e5f4f5',transparent:true,opacity:.22,depthWrite:false,blending:THREE.AdditiveBlending,side:THREE.DoubleSide}));
   jet.rotation.z=socket.down?Math.PI:Math.PI/2;socket.object.add(jet);car.jets.push({mesh:jet,down:socket.down,side:socket.object.position.z<0?-1:1});
  }
 }
 makeEffects(){
  this.captureScene=new PoliceCaptureScene(this.scene,{officer:{near:this.models['CaptureOfficerNear.glb'],mobile:this.models['CaptureOfficerMobile.glb']},driver:{near:this.models['CaptureDriverNear.glb'],mobile:this.models['CaptureDriverMobile.glb']}});
  this.attachJets(this.cars[0]);
  const texels=new Uint8Array(32*32*4);for(let y=0;y<32;y++)for(let x=0;x<32;x++){const i=(y*32+x)*4,r=Math.hypot((x-15.5)/15.5,(y-15.5)/15.5);texels[i]=texels[i+1]=texels[i+2]=255;texels[i+3]=Math.round(255*Math.pow(Math.max(0,1-r),1.4));}this.particleMap=new THREE.DataTexture(texels,32,32);this.particleMap.magFilter=THREE.LinearFilter;this.particleMap.minFilter=THREE.LinearFilter;this.particleMap.needsUpdate=true;
  const geo=new THREE.BufferGeometry();this.dustPositions=new Float32Array(45*3);geo.setAttribute('position',new THREE.BufferAttribute(this.dustPositions,3));this.dust=new THREE.Points(geo,new THREE.PointsMaterial({color:'#d1bc93',size:.25,map:this.particleMap,transparent:true,opacity:.24,depthWrite:false}));this.dust.frustumCulled=false;this.scene.add(this.dust);
  this.sirenGlow=new THREE.PointLight('#427cff',0,18,2);this.scene.add(this.sirenGlow);
  this.vaporPositions=new Float32Array(64*3);const vaporGeometry=new THREE.BufferGeometry();vaporGeometry.setAttribute('position',new THREE.BufferAttribute(this.vaporPositions,3));this.vapor=new THREE.Points(vaporGeometry,new THREE.PointsMaterial({color:'#e8f0ee',size:1.1,map:this.particleMap,transparent:true,opacity:.32,depthWrite:false}));this.vapor.visible=false;this.vapor.frustumCulled=false;this.scene.add(this.vapor);this.vaporAge=10;this.vaporCenter=new THREE.Vector3();
  this.headlamp=new THREE.SpotLight('#fff0d5',0,105,.31,.55,1.1);this.headlamp.target=new THREE.Object3D();this.scene.add(this.headlamp,this.headlamp.target);
 }
 update(model,dt,{menu=false,menuTime=0}={}){
  const worldDt=menu||!model.paused?dt:0;this.clock+=worldDt;if(this.effectModel!==model||(model.state==='countdown'&&this.effectState!=='countdown')){this.effectModel=model;this.lastEffectId=0;this.vaporAge=10;}this.effectState=model.state;for(const event of model.events||[]){if(event.id<=this.lastEffectId)continue;this.lastEffectId=event.id;if(event.type==='landing'){this.vaporAge=0;this.vaporCenter.set(event.x,event.y,event.z);}}this.vaporAge+=worldDt;this.vapor.visible=!menu&&this.vaporAge<1.35;if(this.vapor.visible){const age=this.vaporAge;for(let i=0;i<64;i++){const a=i*2.39996,r=(.4+age*4)*(1+(i%5)*.12);this.vaporPositions[i*3]=this.vaporCenter.x+Math.cos(a)*r;this.vaporPositions[i*3+1]=this.vaporCenter.y+.06+age*.22+(i%7)*.03;this.vaporPositions[i*3+2]=this.vaporCenter.z+Math.sin(a)*r;}this.vapor.geometry.attributes.position.needsUpdate=true;this.vapor.material.opacity=.24*(1-age/1.35);}
  if(this.sky.material?.uniforms?.cloudTime){this.sky.material.uniforms.cloudTime.value=this.clock;this.sky.material.uniforms.night.value=this.night?1:0;}
  this.collectibles?.update(model,dt,{menu});
  this.captureScene?.update(model,{menu,quality:this.quality});
  this.waterShaders.forEach(s=>s.uniforms.waterTime.value=this.clock);this.windShaders.forEach(s=>s.uniforms.windTime.value=this.clock);
  if(!menu&&this.cars[0])applyUpgradeVisuals(this.cars[0],model.upgrades);
  let states=[model.player,...model.rivals,...model.police];
  if(menu){const p=(this.garageMode||this.homeMode)?{x:10000,y:0,z:10000,heading:0,roadPitch:0}:model.sampleRoute(Math.min(this.world?.garage_s??2550,model.routeLength||2550));states=[{...model.player,...p,x:p.x,z:p.z,y:p.y,groundY:p.y,groundHeading:p.heading,groundNormalX:-Math.sin(p.roadPitch||p.pitch||0)*Math.cos(p.heading),groundNormalY:Math.cos(p.roadPitch||p.pitch||0),groundNormalZ:-Math.sin(p.roadPitch||p.pitch||0)*Math.sin(p.heading),grounded:true,groundPitch:p.roadPitch||p.pitch||0,roadPitch:p.roadPitch||p.pitch||0,heading:(this.garageMode||this.homeMode)?(this.homeMode?-.18:(this.garageYaw||0)):(p.heading??Math.atan2(p.tangent?.z||-1,p.tangent?.x||0)),surfaceFrame:null,attached:false,supportPoint:null,groundPoint:null,speed:0,steer:0,wheelAngle:0,stuntRoll:0,flipActive:false,stuntPhase:null,landingAssist:false,flying:false,altitude:0,offRoad:false,bodyRoll:0,bodyPitch:0,suspension:0,thrusting:false,boosting:false,ultraBoosting:false}];}
  this.cars.forEach((v,i)=>{
   let state=states[i];if(i>=4)state=model.police[i-4];else if(i>0)state=model.rivals[i-1];if(menu&&i>0)state=null;
   v.group.visible=!!state&&state.visible!==false;v.contactShadow.visible=v.group.visible;
   if(!state)return;
   const altitude=state.altitude||0;const surfaceBasis=surfaceQuaternion(state.surfaceFrame);if(surfaceBasis){v.contactShadow.visible=v.group.visible&&!!state.attached;const contact=state.supportPoint||state.groundPoint||[state.x,state.y,state.z],normal=state.supportNormal||state.surfaceFrame.up;v.contactShadow.position.fromArray(contact).addScaledVector(new THREE.Vector3(...normal),.014);}else v.contactShadow.position.set(state.x,(state.groundY??((state.y??.18)-altitude))+.014,state.z);v.contactShadow.quaternion.copy(groundOrientation(state)).multiply(SHADOW_FLOOR_ROTATION);v.contactShadow.material.uniforms.opacity.value=.44/(1+altitude*.7);v.contactShadow.scale.setScalar(1+altitude*.12);
   const braking=state.speed>1&&state.speed<v.previousSpeed-.025;for(const lamp of v.brakeLights)lamp.emissiveIntensity=braking?3.5:this.night?1.3:.6;v.previousSpeed=state.speed||0;
   v.group.position.set(state.x,state.y??.18,state.z);if(surfaceBasis)v.group.quaternion.copy(surfaceBasis);else if(state.grounded&&Number.isFinite(state.groundHeading))v.group.quaternion.copy(groundOrientation(state));else v.group.rotation.set(0,-state.heading,state.roadPitch||0);v.stunt.rotation.x=state.stuntRoll||0;
   if(v.chassis){v.chassis.rotation.x=this.reducedMotion?0:clamp(state.bodyRoll||0,-.008,.008);v.chassis.rotation.z=this.reducedMotion?0:clamp(state.bodyPitch||0,-.005,.005);v.chassis.position.y=this.reducedMotion?0:clamp(state.suspension||0,-.002,.002);}
   if(v.wing)v.wing.rotation.z=(state.flying?-.2:(state.boosting||state.ultraBoosting)?-.1:0)-(v.aeroTrimAngle||0);
   for(const jet of v.jets){let active=!menu&&(jet.down?state.thrusting:false);if(!menu&&state.flipActive&&jet.down){if(state.stuntPhase==='roll')active=jet.side<0;if(state.stuntPhase==='counterthrust')active=jet.side>0;}jet.mesh.visible=!!active;jet.mesh.scale.y=(state.landingAssist?1.1:state.ultraBoosting?1.5:.7)+.18*Math.sin(this.clock*39);jet.mesh.material.opacity=.18+.06*Math.sin(this.clock*23);}
   v.boostFire?.update(state,dt,{menu,paused:model.paused,active:model.state==='racing',time:this.clock});
   v.steer.forEach((o,j)=>{if(o)o.rotation.y=j<2?-clamp(state.steer,-(CAR_CATALOG[v.variant]?.maxSteer??.57),CAR_CATALOG[v.variant]?.maxSteer??.57):0;});v.spin.forEach(o=>{if(o)o.rotation.z=-state.wheelAngle;});
   if(v.bar)v.bar.traverse(o=>{if(o.isMesh)for(const m of materialList(o.material)){if(m.name.includes('Red'))m.emissiveIntensity=state.siren?(Math.sin(this.clock*18)>0?4:.15):.05;if(m.name.includes('Blue'))m.emissiveIntensity=state.siren?(Math.sin(this.clock*18)<0?4:.15):.05;}});
  });
  const state=states[0];const pos=new THREE.Vector3(state.x,state.y??.18,state.z);const forward=new THREE.Vector3(Math.cos(state.heading),0,Math.sin(state.heading));const right=new THREE.Vector3(-forward.z,0,forward.x);
  let desired,target,surfaceShot=null,drivingChase=false;
  if(menu){const compact=this.camera.aspect<.9,a=menuTime*.025;
   if(this.garageMode||this.homeMode){let scale=this.homeMode?(compact?1:.82):(compact?1.65:1);const pitch=this.homeMode ? .15 : (this.garagePitch??.21),b=this.homeMode?this.homeViewBounds:this.garageViewBounds,cb=this.canvas?.getBoundingClientRect?.();if(b&&cb?.width&&cb?.height){const t=Math.tan((compact?55:48)*Math.PI/360),fw=clamp(b.width/cb.width,.1,1),fh=clamp(b.height/cb.height,.1,1),distance=Math.max(2.7/(t*this.camera.aspect*fw*.84),(.8+2.7*Math.sin(pitch))/(t*fh*.82));scale=Math.max(scale,distance/Math.hypot(7.5,8.2));}desired=pos.clone().add(new THREE.Vector3(7.5,0,8.2).multiplyScalar(scale));desired.y+=Math.hypot(7.5,8.2)*scale*Math.tan(pitch);target=pos.clone().add(new THREE.Vector3(0,.65,0));}
   else{desired=pos.clone().addScaledVector(forward,7.5*Math.cos(a)).addScaledVector(right,-8.2);if(compact)desired.sub(pos).multiplyScalar(1.65).add(pos);desired.y+=compact?3.5:2.4;target=pos.clone().addScaledVector(forward,-.2);target.y+=.65;}
   if(!(this.garageMode||this.homeMode)||!(this.homeMode?this.homeViewBounds:this.garageViewBounds)){const screenRight=new THREE.Vector3().subVectors(pos,desired).normalize().cross(new THREE.Vector3(0,1,0));target.addScaledVector(screenRight,compact?0:-2.4);}
  }
  else if(model.capture&&['capturing','busted'].includes(model.state)&&this.captureScene){const shot=this.captureScene.camera(model.capture,this.camera.aspect);desired=new THREE.Vector3(...shot.position);target=new THREE.Vector3(...shot.target);}
  else if(this.cinematicPose){desired=new THREE.Vector3(...this.cinematicPose.position);target=new THREE.Vector3(...this.cinematicPose.target);}
  else if(this.landmarkTarget){target=this.getLandmarkPosition(this.landmarkTarget);const portrait=this.camera.aspect<.9?clamp(Number(this.landmarkTarget.portrait_distance_scale)||1.35,1,3):1;desired=target.clone().add(new THREE.Vector3(...(this.landmarkTarget.camera_offset||[25,14,25])).multiplyScalar(portrait));}
  else if(state.surfaceFrame){this.surfaceCamera??=new SurfaceCameraRig();surfaceShot=this.surfaceCamera.update(state,dt,{mode:this.cameraMode,orbitYaw:this.orbitYaw,orbitPitch:this.orbitPitch,reset:this.cameraReset,paused:model.paused,projectSurface:point=>{const q=model.surfaceProject?.(point);return q?{inside:q.insideRange,normal:q.normal||q.up||q.frame?.up,distance:q.signedDistance}:null;}});if(surfaceShot){desired=surfaceShot.position;target=surfaceShot.target;}else{desired=pos.clone().add(new THREE.Vector3(-8,4,0));target=pos.clone();}}
  else if(this.cameraMode===1&&!state.flipActive){const gradeForward=new THREE.Vector3(1,0,0).applyQuaternion(this.cars[0].group.quaternion),gradeUp=new THREE.Vector3(0,1,0).applyQuaternion(this.cars[0].group.quaternion);desired=pos.clone().addScaledVector(gradeForward,1.18).addScaledVector(gradeUp,1.08);target=pos.clone().addScaledVector(gradeForward,35).addScaledVector(gradeUp,.9);}
  else{drivingChase=true;const yaw=state.heading+this.orbitYaw;const back=new THREE.Vector3(Math.cos(yaw),0,Math.sin(yaw));desired=pos.clone().addScaledVector(back,state.flipActive?-11.5:this.cameraMode===2?-10.5:-7.2);desired.y+=this.cameraMode===2?4.1:2.65+this.orbitPitch;target=pos.clone().addScaledVector(forward,4.5*Math.max(0,1-Math.abs(this.orbitYaw)/.6));target.y+=.8;}
  if(surfaceShot)this.camera.up.copy(surfaceShot.up);else{this.camera.up.set(0,1,0);this.surfaceCamera?.reset();}
  const desiredFov=model.capture&&!menu?53:this.cinematicPose&&!menu?this.cinematicPose.fov:this.landmarkTarget&&!menu?(this.landmarkTarget.camera_fov||55):menu?(this.camera.aspect<.9?55:48):this.reducedMotion?61:state.flipActive?82:clamp(61+Math.abs(state.speed||0)*.23+(state.ultraBoosting?6:0),61,state.ultraBoosting?85:79);
  const cameraDt=!menu&&model.paused?0:dt;
  if(drivingChase){this.drivingCamera??=new DrivingCameraFilter();const shot=this.drivingCamera.update(pos,desired,target,desiredFov,cameraDt,{reset:this.cameraReset,paused:model.paused});this.camera.position.copy(shot.position);target=shot.target;this.camera.fov=shot.fov;}
  else{this.drivingCamera?.reset();const ease=(model.capture&&!menu||surfaceShot||this.cinematicPose||this.cameraReset||this.cameraMode===1)?1:1-Math.exp(-cameraDt*6);this.camera.position.lerp(desired,ease);this.camera.fov+=(desiredFov-this.camera.fov)*(model.capture&&!menu||this.cinematicPose?1:1-Math.exp(-cameraDt*3));}
  if(!menu&&!surfaceShot&&!this.cinematicPose&&!this.reducedMotion&&!model.paused){const shake=(state.impactShake||0)*(this.cameraMode===1?.035:.10);this.camera.position.addScaledVector(right,Math.sin(this.clock*71)*shake);this.camera.position.y+=Math.cos(this.clock*59)*shake*.55;}
  this.camera.lookAt(target);this.cameraReset=false;
  const bounds=menu?(this.homeMode?this.homeViewBounds:this.garageMode?this.garageViewBounds:null):null,canvasBounds=this.canvas?.getBoundingClientRect?.();
  if(bounds&&canvasBounds?.width>0&&canvasBounds?.height>0){const cx=bounds.left+bounds.width/2-canvasBounds.left,cy=bounds.top+bounds.height/2-canvasBounds.top;this.camera.setViewOffset(canvasBounds.width,canvasBounds.height,canvasBounds.width/2-cx,canvasBounds.height/2-cy,canvasBounds.width,canvasBounds.height);}
  else if(this.camera.view?.enabled)this.camera.clearViewOffset();this.camera.updateProjectionMatrix();
  const viewFocus=(this.cinematicPose||this.landmarkTarget)&&!menu?target:pos;if(this.garageModel)this.garageModel.visible=!!(this.garageMode||this.homeMode)&&menu;if(this.garageLights)this.garageLights.visible=!!(this.garageMode||this.homeMode)&&menu;if(this.garageModel?.visible)this.showroom?.update(this.clock);if(this.sky)this.sky.visible=!this.garageModel?.visible;
  this.worldTime=(this.worldTime||0)+((model.paused&&!menu)?0:dt);for(const transit of this.transit||[])transit.update(this.worldTime,model.paused&&!menu?0:dt,{night:this.night,viewer:viewFocus});this.dynamicObstacles=(this.transit||[]).flatMap(t=>t.colliderProxies);
  this.sun.position.copy(viewFocus).add(new THREE.Vector3(-50,80,30));this.sun.target.position.copy(viewFocus);this.sky.position.copy(viewFocus);
  for(const chunk of this.environmentChunks){const distance=chunk.userData.center.distanceTo(viewFocus);chunk.visible=distance<(this.quality==='high'?650:420);}
  for(let i=0;i<45;i++){const age=((this.clock*.5+i/45)%1);this.dustPositions[i*3]=state.x-forward.x*(2+age*8)+Math.sin(i*2.4)*age*2;this.dustPositions[i*3+1]=(state.y??.18)+.15+age*.6;this.dustPositions[i*3+2]=state.z-forward.z*(2+age*8)+Math.cos(i*3.7)*age*2;}
  this.dust.geometry.attributes.position.needsUpdate=true;const sliding=Math.abs(state.lateralSpeed||0)>2.4;this.dust.material.color.set(state.offRoad?'#d1bc93':'#b6bdb8');this.dust.visible=!menu&&!state.surfaceFrame&&(state.altitude||0)<.08&&Math.abs(state.speed)>8&&(state.offRoad||sliding);
  const police=model.police.find(p=>p.active!==false);this.sirenGlow.intensity=!menu&&police&&model.wanted?2.5:0;if(police){this.sirenGlow.position.set(police.x,police.y+1.4,police.z);this.sirenGlow.color.set(Math.sin(this.clock*18)>0?'#ef294a':'#3284ff');}
  if(this.checkpointMarker){const gate=model.checkpoints?.[model.nextCheckpoint];this.checkpointMarker.visible=!menu&&model.scenario?.id!=='free-drive'&&!!gate&&['countdown','racing'].includes(model.state);if(gate){this.checkpointMarker.position.set(gate.x,gate.y,gate.z);this.checkpointMarker.rotation.y=-gate.heading;}}
  const lampForward=new THREE.Vector3(1,0,0).applyQuaternion(this.cars[0].group.quaternion),lampUp=new THREE.Vector3(0,1,0).applyQuaternion(this.cars[0].group.quaternion);this.headlamp.position.copy(pos).addScaledVector(lampForward,2.05).addScaledVector(lampUp,.6);this.headlamp.target.position.copy(pos).addScaledVector(lampForward,45).addScaledVector(lampUp,.05);this.headlamp.intensity=this.night&&!menu?55:0;
  for(const field of this.detailFields||[])field.update(this.camera.position,worldDt,this.quality);
  this.detailStats={enabled:!!this.detailFields?.length,instances:0,triangles:0,draws:0,teaRadius:0,treeRadius:0};for(const field of this.detailFields||[]){const d=field.stats;this.detailStats.instances+=d.instances;this.detailStats.triangles+=d.triangles;this.detailStats.draws+=d.draws;this.detailStats[d.name==='tea'?'teaRadius':'treeRadius']=d.radius;}
  this.presentation?.update(model,worldDt,{menu:menu||!!state.surfaceFrame,quality:this.quality,camera:this.camera});
  this.airTraffic?.update(model,{menu,quality:this.quality,night:this.night});
  this.simReadyPilot?.update(this.camera,{menu,quality:this.quality});
  this.roadLighting?.update(model,{menu});
  this.renderer.render(this.scene,this.camera);
 }
 resize(){const w=this.canvas.clientWidth||innerWidth,h=this.canvas.clientHeight||innerHeight;this.renderer.setPixelRatio(renderPixelRatio(devicePixelRatio||1,this.quality,this.resolutionMode));this.resolutionRevision=(this.resolutionRevision||0)+1;this.renderer.setSize(w,h,false);this.camera.aspect=w/h;this.camera.updateProjectionMatrix();}
 setResolution(mode){if(!RENDER_RESOLUTIONS.includes(mode))return false;this.resolutionMode=mode;this.resize();return true;}
 get resolutionDiagnostics(){const size=this.renderer.getDrawingBufferSize(new THREE.Vector2());return{mode:this.resolutionMode||'auto',cssWidth:this.canvas.clientWidth||innerWidth,cssHeight:this.canvas.clientHeight||innerHeight,deviceRatio:devicePixelRatio||1,pixelRatio:this.renderer.getPixelRatio(),bufferWidth:size.x,bufferHeight:size.y,antialias:!!this.actualAntialias,shadows:!!this.renderer.shadowMap.enabled,shadowSize:this.sun.shadow.mapSize.x,revision:this.resolutionRevision||0};}
 setQuality(value){this.quality=value;this.renderer.shadowMap.enabled=value==='high';this.resize();}
 orbitGarage(deltaYaw,deltaPitch=0){if(!this.garageMode)return false;this.garageYaw=Math.atan2(Math.sin((this.garageYaw||0)+(Number.isFinite(deltaYaw)?deltaYaw:0)),Math.cos((this.garageYaw||0)+(Number.isFinite(deltaYaw)?deltaYaw:0)));this.garagePitch=clamp((this.garagePitch??.21)+(Number.isFinite(deltaPitch)?deltaPitch:0),.10,.40);this.cameraReset=true;return true;}
 resetGarageView(){this.garageYaw=0;this.garagePitch=.21;this.cameraReset=true;}
 setGarageViewBounds(bounds){this.garageViewBounds=bounds&&['left','top','width','height'].every(k=>Number.isFinite(bounds[k]))&&bounds.width>0&&bounds.height>0?{left:bounds.left,top:bounds.top,width:bounds.width,height:bounds.height}:null;this.cameraReset=true;}
 setHomeViewBounds(bounds){this.homeViewBounds=bounds&&['left','top','width','height'].every(k=>Number.isFinite(bounds[k]))&&bounds.width>0&&bounds.height>0?{left:bounds.left,top:bounds.top,width:bounds.width,height:bounds.height}:null;this.cameraReset=true;}
 _syncShowroomLighting(){const active=!!(this.garageMode||this.homeMode);if(this.showroomEnvironment&&this.coastalEnvironment)this.scene.environment=active?this.showroomEnvironment:this.coastalEnvironment;if(active&&!this.garageLighting&&this.sun&&this.hemisphere){this.garageLighting={sun:this.sun.intensity,hemisphere:this.hemisphere.intensity,sunColor:this.sun.color.clone(),skyColor:this.hemisphere.color.clone(),groundColor:this.hemisphere.groundColor.clone(),exposure:this.renderer?.toneMappingExposure};this.sun.intensity=.55;this.hemisphere.intensity=.9;this.sun.color.set('#d58b46');this.hemisphere.color.set('#677b91');this.hemisphere.groundColor.set('#20232a');if(this.renderer)this.renderer.toneMappingExposure=.92;}else if(!active&&this.garageLighting){this.sun.intensity=this.garageLighting.sun;this.hemisphere.intensity=this.garageLighting.hemisphere;this.sun.color.copy(this.garageLighting.sunColor);this.hemisphere.color.copy(this.garageLighting.skyColor);this.hemisphere.groundColor.copy(this.garageLighting.groundColor);if(this.renderer)this.renderer.toneMappingExposure=this.garageLighting.exposure;this.garageLighting=null;}}
 setHomeMode(enabled){this.homeMode=!!enabled;if(this.homeMode)this.garageMode=false;this._syncShowroomLighting();this.landmarkTarget=null;this.cameraReset=true;return this.homeMode;}
 setGarageMode(enabled){enabled=!!enabled;if(enabled&&!this.garageMode)this.resetGarageView();this.garageMode=enabled;if(enabled)this.homeMode=false;this._syncShowroomLighting();this.landmarkTarget=null;this.cameraReset=true;return this.garageMode;}

 getLandmarkPosition(target){
  const transit=target?.transit_id?(this.transit||[]).find(t=>t.config.id===target.transit_id):null;
  if(transit){const object=transit.carriages?.length?transit.carriages[transit.state?.direction<0?2:0].pivot:transit.group;return object.position.clone().add(new THREE.Vector3(0,2,0));}
  return new THREE.Vector3(...(target?.position||[0,0,0]));
 }
 setPlayerUpgrades(upgrades){if(!this.cars[0])return false;return applyUpgradeVisuals(this.cars[0],upgrades);}
 setCinematicCamera(pose){if(pose===null){this.cinematicPose=null;this.cameraReset=true;return true;}if(!validCinematicPose(pose))return false;this.cinematicPose={position:[...pose.position],target:[...pose.target],fov:pose.fov};return true;}
 lookAtLandmark(target){this.landmarkTarget=target?.position?.length===3&&target.position.every(Number.isFinite)?target:null;this.cameraReset=true;if(this.landmarkTarget&&this.camera){this.camera.fov=this.landmarkTarget.camera_fov||55;this.camera.updateProjectionMatrix();}return !!this.landmarkTarget;}
 cycleCamera(){this.landmarkTarget=null;this.cameraMode=(this.cameraMode+1)%3;this.cameraReset=true;this.orbitYaw=0;return ['CHASE','BONNET','WIDE'][this.cameraMode];}
 dispose(){this.captureScene?.dispose();this.showroom?.dispose();this.airTraffic?.dispose();this.renderer.dispose();}
}
