/** Exact prebuilt asset package; bounded streaming only, never a filesystem fallback. */
import {createReadStream,constants} from 'node:fs';
import {lstat,readFile,realpath,open} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {resolve,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {performance} from 'node:perf_hooks';
const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.glb':'model/gltf-binary','.ttf':'font/ttf','.woff':'font/woff','.woff2':'font/woff2','.txt':'text/plain; charset=utf-8'};
const safePath=p=>typeof p==='string'&&p.length<240&&p.split('/').every(s=>/^[A-Za-z0-9_-][A-Za-z0-9_.-]*$/.test(s));
const approved=p=>['online.html','online.js','online.css','licenses.html'].includes(p)||/^assets\/[A-Za-z0-9_-][A-Za-z0-9_.-]*\.(?:glb|json|ttf|woff2?)$/.test(p)||/^licenses\/[A-Za-z0-9_-][A-Za-z0-9_.-]*\.txt$/.test(p);
const rootPath=root=>root instanceof URL?fileURLToPath(root):resolve(root);
async function checkedFile(base,name){
 const baseInfo=await lstat(base);if(baseInfo.isSymbolicLink()||!baseInfo.isDirectory())throw Error('Static root denied');const root=await realpath(base);let current=root;for(const part of name.split('/')){current=resolve(current,part);const s=await lstat(current);if(s.isSymbolicLink())throw Error('Static symlink denied');if(current!==resolve(root,name)&&!s.isDirectory())throw Error('Static parent is not a directory');}
 const actual=await realpath(current),rel=relative(root,actual);if(rel.startsWith('..'+sep)||rel==='..'||rel.startsWith(sep))throw Error('Static path escaped root');const stat=await lstat(actual);if(!stat.isFile())throw Error('Static asset is not a file');return{path:actual,stat};
}
export async function readStaticAllowlist(root){const base=rootPath(root),file=await checkedFile(base,'public-manifest.json');if(file.stat.size>200000)throw Error('Static manifest too large');const value=JSON.parse(await readFile(file.path,'utf8'));if(value.schemaVersion!==1||!Array.isArray(value.files))throw Error('Invalid static manifest');return value.files;}
export async function loadStaticAssets(root,entries,{maxStreams=16,byteCapacity=64*1024*1024,bytesPerSecond=128*1024,now=()=>performance.now()}={}){
 if(!Array.isArray(entries)||entries.length<1||entries.length>256||!Number.isSafeInteger(maxStreams)||maxStreams<1||!Number.isFinite(byteCapacity)||byteCapacity<1||!Number.isFinite(bytesPerSecond)||bytesPerSecond<=0)throw Error('Invalid static limits');
 const base=resolve(rootPath(root),'public'),assets=new Map();let total=0;
 for(const entry of entries){
  if(!entry||Object.keys(entry).sort().join(',')!=='bytes,path,sha256,url'||!safePath(entry.path)||!approved(entry.path)||entry.url!==(entry.path.startsWith('assets/')?'/public/':'/')+entry.path||!Number.isSafeInteger(entry.bytes)||entry.bytes<0||entry.bytes>24*1024*1024||!/^[0-9a-f]{64}$/.test(entry.sha256)||assets.has(entry.url))throw Error('Invalid static allowlist entry');
  total+=entry.bytes;if(total>64*1024*1024)throw Error('Static package too large');const file=await checkedFile(base,entry.path);if(file.stat.size!==entry.bytes)throw Error('Static size mismatch');const hash=createHash('sha256');for await(const chunk of createReadStream(file.path))hash.update(chunk);if(hash.digest('hex')!==entry.sha256)throw Error('Static hash mismatch');
  const extension=entry.path.slice(entry.path.lastIndexOf('.'));assets.set(entry.url,{...entry,...file,relativePath:entry.path,type:MIME[extension],etag:'"'+entry.sha256+'"'});
 }
 if(!assets.has('/online.html'))throw Error('Online entry missing');assets.set('/',assets.get('/online.html'));const offer=assets.get('/public/assets/coastal_map_data.json');if(offer)assets.set('/map-data',offer);
 let active=0,available=byteCapacity,previous=now();const refill=()=>{const t=now();available=Math.min(byteCapacity,available+Math.max(0,t-previous)*bytesPerSecond/1000);previous=t;};
 function serve(req,res){
  const asset=assets.get(req.url);if(!asset)return false;
  res.setHeader('Content-Type',asset.type);res.setHeader('ETag',asset.etag);res.setHeader('Cache-Control','no-cache');
  if(req.headers['if-none-match']===asset.etag||req.headers['if-none-match']==='*'){res.writeHead(304);res.end();return true;}
  refill();if(active>=maxStreams||asset.bytes>available){res.writeHead(429,{'Retry-After':String(active>=maxStreams?1:Math.max(1,Math.ceil((asset.bytes-available)/bytesPerSecond)))});res.end('Static bandwidth busy');return true;}
  available-=asset.bytes;active++;let released=false,stream;
  const release=()=>{if(released)return;released=true;active--;stream?.destroy();};res.once('finish',release);res.once('close',release);res.once('error',release);
  void(async()=>{let handle;try{
   if(released)return;const current=await checkedFile(base,asset.relativePath);handle=await open(current.path,constants.O_RDONLY|constants.O_NOFOLLOW);const s=await handle.stat();if(s.size!==asset.bytes||s.ino!==asset.stat.ino||s.dev!==asset.stat.dev||s.mtimeMs!==asset.stat.mtimeMs)throw Error('Static file changed after verification');
   if(released){await handle.close();return;}res.setHeader('Content-Length',asset.bytes);stream=handle.createReadStream({highWaterMark:64*1024});handle=null;stream.on('error',()=>{if(!res.headersSent){res.writeHead(503);res.end('Static asset unavailable');}else res.destroy();release();});stream.pipe(res);
  }catch{if(handle)await handle.close().catch(()=>{});if(!released){if(!res.headersSent){res.writeHead(503);res.end('Static asset unavailable');}else res.destroy();release();}}})();return true;
 }
 return{serve,get count(){return entries.length;},get activeStreams(){return active;}};
}
