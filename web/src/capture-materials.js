/** Bounded original material pass. No textures, geometry or physics are replaced. */
import * as THREE from 'three';
export function refineCarPaint(material,paintName){
 if(material.name!==paintName)return material;
 const paint=new THREE.MeshPhysicalMaterial();THREE.MeshStandardMaterial.prototype.copy.call(paint,material);
 paint.clearcoat=.72;paint.clearcoatRoughness=.19;return paint;
}
export function refineFacade(material){
 if(!/plaster|concrete|stucco/i.test(material.name)||material.userData.captureFacade)return false;
 material.userData.captureFacade=true;material.roughness=.92;
 const previous=material.onBeforeCompile,cache=material.customProgramCacheKey.bind(material);
 const key=cache();material.onBeforeCompile=function(shader,...args){
  previous.call(this,shader,...args);
  shader.vertexShader='varying vec3 vFacadePoint;\n'+shader.vertexShader;
  shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvFacadePoint=position;');
  shader.fragmentShader='varying vec3 vFacadePoint;\n'+shader.fragmentShader;
  shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\nfloat wear=sin(vFacadePoint.y*9.7+sin(vFacadePoint.x*7.1+vFacadePoint.z*4.3));\nfloat filteredWear=wear*(1.-smoothstep(.04,.3,length(fwidth(vFacadePoint))));\ndiffuseColor.rgb*=.97+.025*filteredWear;');
 };material.customProgramCacheKey=()=>key+'-capture-facade-v1';material.needsUpdate=true;return true;
}
