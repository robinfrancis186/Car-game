/** Original procedural asphalt, adapted from the preserved Draft 2 experiment. */
import * as THREE from 'three';
let maps;
const hash=(x,y)=>{let h=Math.imul(x+17,374761393)^Math.imul(y+31,668265263);h=Math.imul(h^(h>>>13),1274126177);return((h^(h>>>16))>>>0)/4294967296;};
export function arrestAsphaltMaps(){
 if(maps)return maps;
 const size=512,height=new Float32Array(size*size),color=new Uint8Array(size*size*4),rough=new Uint8Array(size*size*4),normal=new Uint8Array(size*size*4);
 const noise=(x,y,n)=>{const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy,u=fx*fx*(3-2*fx),v=fy*fy*(3-2*fy),at=(a,b)=>hash((a+n)%n,(b+n)%n);return THREE.MathUtils.lerp(THREE.MathUtils.lerp(at(ix,iy),at(ix+1,iy),u),THREE.MathUtils.lerp(at(ix,iy+1),at(ix+1,iy+1),u),v);};
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){
  const i=y*size+x,macro=noise(x/64,y/64,8),aggregate=noise(x/4,y/4,128),grain=hash(x,y),chip=Math.max(0,aggregate-.58);
  const level=Math.round(44+macro*6+aggregate*5+(grain-.5)*5+chip*14),r=Math.round(202+macro*30+aggregate*18);
  color.set([level,level+2,level+3,255],i*4);rough.set([r,r,r,255],i*4);height[i]=(grain-.5)*.12+(aggregate-.5)*.55+chip*.35;
 }
 const at=(x,y)=>height[((y+size)%size)*size+(x+size)%size];
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){const n=new THREE.Vector3(-(at(x+1,y)-at(x-1,y))*.2,-(at(x,y+1)-at(x,y-1))*.2,1).normalize();normal.set([Math.round((n.x*.5+.5)*255),Math.round((n.y*.5+.5)*255),Math.round((n.z*.5+.5)*255),255],(y*size+x)*4);}
 const texture=(data,srgb=false)=>{const t=new THREE.DataTexture(data,size,size);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.minFilter=THREE.LinearMipmapLinearFilter;t.magFilter=THREE.LinearFilter;t.generateMipmaps=true;t.colorSpace=srgb?THREE.SRGBColorSpace:THREE.NoColorSpace;t.needsUpdate=true;return t;};
 maps={albedo:texture(color,true),roughness:texture(rough),normal:texture(normal),size,bytes:color.byteLength+rough.byteLength+normal.byteLength};return maps;
}
export class RoadLighting{
 constructor(r,{center,heading=0}){
  if(r.roadLighting)throw Error('Only one arrest road draft may be active');
  this.r=r;r.roadLighting=this;this.changed=[];this.materials=[];this.maps=arrestAsphaltMaps();
  this.uniforms={roadLightStrength:{value:0},arrestCenter:{value:new THREE.Vector2(center.x,center.z)},arrestForward:{value:new THREE.Vector2(Math.cos(heading),Math.sin(heading))},arrestAlbedo:{value:this.maps.albedo},arrestRough:{value:this.maps.roughness},arrestNormal:{value:this.maps.normal}};
  const clones=new Map();r.scene.traverse(o=>{if(!o.isMesh||!o.name.startsWith('Course_Road'))return;const original=o.material,list=Array.isArray(original)?original:[original];let changed=false;
   const next=list.map(m=>{const asphalt=/asphalt/i.test(m.name),marking=/weatheredwhite/i.test(m.name);if(!asphalt&&!marking)return m;changed=true;if(clones.has(m))return clones.get(m);const draft=m.clone(),prior=m.onBeforeCompile,key=m.customProgramCacheKey();
    draft.onBeforeCompile=(s,gpu)=>{prior.call(m,s,gpu);Object.assign(s.uniforms,this.uniforms);
     s.vertexShader='varying vec3 vArrestWorld;\n'+s.vertexShader;s.vertexShader=s.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nvArrestWorld=(modelMatrix*vec4(transformed,1.)).xyz;');
     const lighting=THREE.ShaderChunk.lights_fragment_begin.replace('directionalLightShadow = directionalLightShadows[ i ];','directionalLightShadow = directionalLightShadows[ i ];\ndirectionalLightShadow.shadowIntensity *= 1.-roadLightStrength*smoothstep(50.,80.,length(vArrestWorld.xz-arrestCenter));');
     s.fragmentShader=s.fragmentShader.replace('#include <lights_fragment_begin>',lighting);
     s.fragmentShader='uniform float roadLightStrength;varying vec3 vArrestWorld;uniform vec2 arrestCenter;uniform vec2 arrestForward;uniform sampler2D arrestAlbedo;uniform sampler2D arrestRough;uniform sampler2D arrestNormal;\n'+s.fragmentShader;
     const body=`float arrestMask=roadLightStrength*(1.-smoothstep(18.,30.,length(vArrestWorld.xz-arrestCenter)));vec2 arrestUV=vArrestWorld.xz/2.4;float lateral=dot(vArrestWorld.xz-arrestCenter,vec2(-arrestForward.y,arrestForward.x));float wheelWear=1.-smoothstep(.2,.52,abs(abs(lateral)-.72));`;
     const albedo=asphalt?'texture2D(arrestAlbedo,arrestUV).rgb*(1.-wheelWear*.055)':'vec3(.63,.63,.59)*(0.97+texture2D(arrestRough,arrestUV).g*.03)';
     s.fragmentShader=s.fragmentShader.replace('#include <alphamap_fragment>',body+`diffuseColor.rgb=mix(diffuseColor.rgb,${albedo},arrestMask);\n#include <alphamap_fragment>`);
     s.fragmentShader=s.fragmentShader.replace('#include <metalnessmap_fragment>',`roughnessFactor=mix(roughnessFactor,${asphalt?'clamp(texture2D(arrestRough,arrestUV).g-wheelWear*.055,.73,.98)':'.83'},arrestMask);\n#include <metalnessmap_fragment>`);
     if(asphalt)s.fragmentShader=s.fragmentShader.replace('#include <normal_fragment_maps>','#include <normal_fragment_maps>\nvec2 grainSlope=(texture2D(arrestNormal,arrestUV).rg*2.-1.)*.25;normal=normalize(normal+mat3(viewMatrix)*vec3(grainSlope.x,0.,grainSlope.y)*arrestMask);');
    };draft.customProgramCacheKey=()=>key+'-road-lighting-pilot-'+asphalt;draft.needsUpdate=true;clones.set(m,draft);this.materials.push(draft);return draft;});
   if(changed){this.changed.push({object:o,original});o.material=Array.isArray(original)?next:next[0];}
  });
  const sky=r.sky.material;sky.uniforms.roadSunDirection={value:new THREE.Vector3(-.5,.25,.65)};sky.fragmentShader='uniform vec3 roadSunDirection;\n'+sky.fragmentShader.replace('normalize(vec3(-.5,.25,.65))','normalize(roadSunDirection)');sky.needsUpdate=true;
  const sun=r.sun,hemi=r.hemisphere,camera=sun.shadow.camera;
  this.lighting={sunColor:sun.color.clone(),sunIntensity:sun.intensity,sunPosition:sun.position.clone(),sky:hemi.color.clone(),ground:hemi.groundColor.clone(),hemiIntensity:hemi.intensity,exposure:r.renderer.toneMappingExposure,normalBias:sun.shadow.normalBias,bias:sun.shadow.bias,frustum:[camera.left,camera.right,camera.top,camera.bottom],depth:[camera.near,camera.far]};

 }
 reset(){const r=this.r,s=this.lighting,c=r.sun.shadow.camera;r.sun.color.copy(s.sunColor);r.hemisphere.color.copy(s.sky);r.hemisphere.groundColor.copy(s.ground);[c.left,c.right,c.top,c.bottom]=s.frustum;[c.near,c.far]=s.depth;c.updateProjectionMatrix();r.sun.shadow.normalBias=s.normalBias;r.sun.shadow.bias=s.bias;this.uniforms.roadLightStrength.value=0;this.active=false;r.sky.material.uniforms.roadSunDirection?.value.set(-.5,.25,.65);}
 update(model,{menu=false}={}){
  const r=this.r,s=this.lighting,c=r.sun.shadow.camera,active=!menu&&!r.night&&!model.player.surfaceFrame;
  this.uniforms.roadLightStrength.value=active?1:0;if(!active)return;
  this.active=true;const p=model.player;this.uniforms.arrestCenter.value.set(p.x,p.z);this.uniforms.arrestForward.value.set(Math.cos(p.heading),Math.sin(p.heading));
  r.sky.material.uniforms.roadSunDirection?.value.set(-.5,.55,.65);r.sun.position.copy(r.sun.target.position).add(new THREE.Vector3(-50,55,65));r.sun.color.set('#fff0dc');r.sun.intensity=r.lightingMode==='hot-pursuit'?1.7:3.1;r.hemisphere.color.set('#d6e2ec');r.hemisphere.groundColor.set('#686553');r.hemisphere.intensity=r.lightingMode==='hot-pursuit'?1.6:2.15;r.renderer.toneMappingExposure=1.03;
  r.sun.shadow.normalBias=.02;r.sun.shadow.bias=-.00015;c.left=c.bottom=-85;c.right=c.top=85;c.near=1;c.far=350;c.updateProjectionMatrix();
 }
}
