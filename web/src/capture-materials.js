/** Bounded original material pass. No textures, geometry or physics are replaced. */
import * as THREE from 'three';
import {refineSceneryMaterial} from './scenery-materials.js';
export function refineCarPaint(material,paintName){
 if(material.name!==paintName)return material;
 const paint=new THREE.MeshPhysicalMaterial();THREE.MeshStandardMaterial.prototype.copy.call(paint,material);
 paint.clearcoat=.72;paint.clearcoatRoughness=.19;return paint;
}
export function refineFacade(material){
 if(!/plaster|concrete|stucco/i.test(material.name)||material.userData.captureFacade)return false;
 material.userData.captureFacade=true;material.roughness=.92;
 return refineSceneryMaterial(material,'facade');
}
