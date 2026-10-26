import fs from 'node:fs/promises';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
// Geometry/skeleton fixture only: real encoded textures are decoded by browser QA.
export async function captureAssets(){
 globalThis.ProgressEvent??=class{constructor(type,fields){this.type=type;Object.assign(this,fields);}};
 const models={};for(const role of ['Officer','Driver'])for(const lod of ['Near','Mobile']){
  const name=`Capture${role}${lod}.glb`,bytes=await fs.readFile(new URL('../public/assets/'+name,import.meta.url)),n=bytes.readUInt32LE(12),data=JSON.parse(bytes.toString('utf8',20,20+n)),offset=20+n,bin=bytes.subarray(offset+8,offset+8+bytes.readUInt32LE(offset));
  data.images=[];data.textures=[];for(const m of data.materials){delete m.pbrMetallicRoughness?.baseColorTexture;delete m.pbrMetallicRoughness?.metallicRoughnessTexture;delete m.normalTexture;delete m.occlusionTexture;delete m.emissiveTexture;}
  data.buffers[0].uri='data:application/octet-stream;base64,'+bin.toString('base64');models[name]=(await new GLTFLoader().parseAsync(JSON.stringify(data),'')).scene;
 }return models;
}
export const captureTemplates=models=>({officer:{near:models['CaptureOfficerNear.glb'],mobile:models['CaptureOfficerMobile.glb']},driver:{near:models['CaptureDriverNear.glb'],mobile:models['CaptureDriverMobile.glb']}});

export async function imageHeader(blob){
 const b=Buffer.from(await blob.arrayBuffer());let width,height;
 if(b.toString('hex',0,8)==='89504e470d0a1a0a'){width=b.readUInt32BE(16);height=b.readUInt32BE(20);}
 else{if(b.readUInt16BE(0)!==0xffd8)throw Error('Unknown fixture image header');for(let i=2;i+8<b.length;){const marker=b[i+1],length=b.readUInt16BE(i+2);if(marker===0xc0||marker===0xc2){height=b.readUInt16BE(i+5);width=b.readUInt16BE(i+7);break;}i+=length+2;}if(!width||!height)throw Error('Missing JPEG frame header');}
 return{width,height,close(){}};
}
