/** Original deterministic surface detail. No downloaded imagery, new meshes or collisions. */
import * as THREE from 'three';
let detail;
export function sceneryDetailTexture(){
 if(detail)return detail;
 const size=256,data=new Uint8Array(size*size*4);let seed=0x4b455241;
 const random=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return(seed>>>0)/4294967296;};
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){
  const i=(y*size+x)*4,g=random();
  data.set([Math.round(g*255),Math.round(190+g*54),Math.round(random()*35),255],i);
 }
 for(let i=0;i<3000;i++){const x=random()*size,y=random()*size,a=random()*Math.PI*2,length=4+random()*10;for(let t=0;t<length;t++){const px=(Math.round(x+Math.cos(a)*t)+size)%size,py=(Math.round(y+Math.sin(a)*t)+size)%size,j=(py*size+px)*4+2;data[j]=Math.max(data[j],Math.round(240*Math.sin(Math.PI*(t+.5)/length)));}}
 detail=new THREE.DataTexture(data,size,size);detail.wrapS=detail.wrapT=THREE.RepeatWrapping;detail.minFilter=THREE.LinearMipmapLinearFilter;detail.magFilter=THREE.LinearFilter;detail.generateMipmaps=true;detail.colorSpace=THREE.NoColorSpace;detail.anisotropy=2;detail.needsUpdate=true;return detail;
}
export const facadeTintKind=name=>/warm_?lime_plaster/i.test(name)?'facade_color':/kerala_teal_trim/i.test(name)?'accent_color':null;
const villagePalette=['#d7d0b8','#d5c3a2','#bdc9bc','#d3c5b4','#c0cace'];
export function fallbackFacadeColor(placement,original){
 if(placement.asset!=='KeralaHouse')return original;
 const [x,,z]=placement.position,seed=Math.imul(Math.round(x*10),73856093)^Math.imul(Math.round(z*10),19349663);
 return villagePalette[(seed>>>0)%villagePalette.length];
}
const noise=`float scHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}float scNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(scHash(i),scHash(i+vec2(1,0)),f.x),mix(scHash(i+vec2(0,1)),scHash(i+vec2(1)),f.x),f.y);}`;
export function refineSceneryMaterial(material,kind){
 if(material.userData.scenerySurface)return false;material.userData.scenerySurface=kind;
 const previous=material.onBeforeCompile,key=material.customProgramCacheKey(),texture=sceneryDetailTexture(),local=kind==='facade'?'vFacadePoint':'vScLocal';
 material.onBeforeCompile=function(shader,...args){
  previous.call(this,shader,...args);shader.uniforms??={};shader.uniforms.sceneryDetail={value:texture};
  shader.vertexShader=`varying vec3 vScWorld;varying vec3 ${local};\n`+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>\n${local}=position;`);
  shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nvec4 scWorld=vec4(transformed,1.);\n#ifdef USE_INSTANCING\nscWorld=instanceMatrix*scWorld;\n#endif\nvScWorld=(modelMatrix*scWorld).xyz;');
  shader.fragmentShader=`varying vec3 vScWorld;varying vec3 ${local};uniform sampler2D sceneryDetail;${noise}\n`+shader.fragmentShader;
  let color,height,rough;
  if(kind==='ground'){
   color=`float scMacro=scNoise(vScWorld.xz*.055),scPatch=scNoise(vScWorld.xz*.37);vec4 scTex=texture2D(sceneryDetail,vScWorld.xz*.38);float scSoil=smoothstep(.56,.78,scMacro*.55+scPatch*.45);vec3 scGrass=mix(vec3(.035,.075,.014),vec3(.11,.17,.045),smoothstep(.2,.8,scMacro));diffuseColor.rgb=mix(scGrass,vec3(.15,.105,.055),scSoil*.62)*(.86+scTex.b*.26);`;
   height='scTex.b*.035';rough='.96';
  }else if(kind==='foliage'){
   color='float scVariation=scNoise(vScWorld.xz*.075);vec4 scTex=texture2D(sceneryDetail,vScWorld.xz*.7+vScWorld.y*.13);diffuseColor.rgb*=mix(vec3(.69,.80,.59),vec3(1.04,.98,.78),scVariation)*(.92+scTex.r*.12);';
   height=null;rough='.88';
  }else if(kind==='facade'){
   color=`vec2 scPlane=vec2(${local}.x+${local}.z,${local}.y);float scStain=scNoise(scPlane*vec2(.8,.075)),scDamp=(1.-smoothstep(.2,1.6,${local}.y))*(.5+.5*scStain);vec4 scTex=texture2D(sceneryDetail,scPlane*1.6);scTex.r=mix(scTex.r,.5,smoothstep(.8,2.,length(fwidth(scPlane*1.6))));diffuseColor.rgb*=mix(vec3(.97),vec3(.76,.79,.71),scDamp)*(.945+.055*scStain)*(.97+.06*scTex.r);`;
   height='scTex.r*.006';rough='.90+scTex.r*.08';
  }else{
   color='vec4 scTex=texture2D(sceneryDetail,vScWorld.xz*.8);float scPatch=scNoise(vScWorld.xz*.22);diffuseColor.rgb*=(.88+.14*scPatch)*(.92+.16*scTex.r);';height=kind==='gravel'?'scTex.r*.018':'scTex.r*.008';rough='.94';
  }
  shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\n'+color);
  shader.fragmentShader=shader.fragmentShader.replace('#include <roughnessmap_fragment>',`#include <roughnessmap_fragment>\nroughnessFactor=clamp(${rough},.75,1.);`);
  if(height)shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>\nfloat scHeight=${height};vec3 scDx=dFdx(-vViewPosition),scDy=dFdy(-vViewPosition),scR1=cross(scDy,normal),scR2=cross(normal,scDx);float scDet=dot(scDx,scR1);vec3 scGrad=sign(scDet)*(dFdx(scHeight)*scR1+dFdy(scHeight)*scR2);normal=normalize(max(abs(scDet),1.e-8)*normal-scGrad);`);
 };material.customProgramCacheKey=()=>key+'-scenery-v2-'+kind;material.needsUpdate=true;return true;
}
