/** Original procedural micro-surfaces; no downloaded textures or extra draw calls. */
import * as THREE from 'three';
let roadMaps;
export function asphaltMicroMaps(){
 if(roadMaps)return roadMaps;
 const size=128,height=new Float32Array(size*size),rough=new Uint8Array(size*size*4),normal=new Uint8Array(size*size*4);
 let seed=0x4d414c41;const random=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return(seed>>>0)/4294967296;};
 for(let i=0;i<height.length;i++){const grain=random(),pit=random();height[i]=grain*.35+(pit>.96?.55:0);const v=Math.round(190+grain*54);rough.set([v,v,v,255],i*4);}
 const at=(x,y)=>height[((y+size)%size)*size+(x+size)%size];
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){const dx=(at(x+1,y)-at(x-1,y))*.28,dy=(at(x,y+1)-at(x,y-1))*.28,v=new THREE.Vector3(-dx,-dy,1).normalize();normal.set([Math.round((v.x*.5+.5)*255),Math.round((v.y*.5+.5)*255),Math.round((v.z*.5+.5)*255),255],(y*size+x)*4);}
 const texture=data=>{const t=new THREE.DataTexture(data,size,size);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.magFilter=THREE.LinearFilter;t.minFilter=THREE.LinearMipmapLinearFilter;t.generateMipmaps=true;t.needsUpdate=true;return t;};
 roadMaps={normalMap:texture(normal),roughnessMap:texture(rough)};return roadMaps;
}
export function applyRoadMicroSurface(mesh){
 const ms=Array.isArray(mesh.material)?mesh.material:[mesh.material];if(!ms.some(m=>/asphalt/i.test(m.name)))return false;
 if(!mesh.geometry.attributes.uv){mesh.updateWorldMatrix(true,false);const p=mesh.geometry.attributes.position,uv=new Float32Array(p.count*2),v=new THREE.Vector3();for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld);uv[i*2]=v.x*.5;uv[i*2+1]=v.z*.5;}mesh.geometry.setAttribute('uv',new THREE.BufferAttribute(uv,2));}
 const maps=asphaltMicroMaps();for(const m of ms)if(/asphalt/i.test(m.name)){m.normalMap=maps.normalMap;m.normalScale.set(.32,.32);m.roughnessMap=maps.roughnessMap;m.roughness=1;m.needsUpdate=true;}return true;
}
export function makeCoastalReflectionScene(){
 const scene=new THREE.Scene(),g=new THREE.SphereGeometry(60,32,20),p=g.attributes.position,colors=[];
 const top=new THREE.Color('#7cabc6'),horizon=new THREE.Color('#d9d6c3'),earth=new THREE.Color('#59604b');
 for(let i=0;i<p.count;i++){const y=p.getY(i)/60,c=y>=0?horizon.clone().lerp(top,Math.pow(y,.55)):horizon.clone().lerp(earth,Math.min(1,-y*4));colors.push(c.r,c.g,c.b);}
 g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));scene.add(new THREE.Mesh(g,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.BackSide})));
 const sun=new THREE.Mesh(new THREE.SphereGeometry(2.4,16,12),new THREE.MeshBasicMaterial({color:new THREE.Color('#fff0d4').multiplyScalar(4)}));sun.position.set(-23,37,18);scene.add(sun);return scene;
}
