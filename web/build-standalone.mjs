import {build} from 'esbuild';
import {readFile,writeFile,readdir,mkdir} from 'node:fs/promises';
import path from 'node:path';
const root=path.dirname(new URL(import.meta.url).pathname);const out=path.resolve(root,'../dist');await mkdir(out,{recursive:true});
const result=await build({entryPoints:[path.join(root,'src/main.js')],absWorkingDir:root,bundle:true,format:'iife',platform:'browser',write:false,minify:true,target:'es2022',legalComments:'eof'});
let html=await readFile(path.join(root,'index.html'),'utf8'),css=await readFile(path.join(root,'src/style.css'),'utf8');
const font=(await readFile(path.join(root,'public/assets/fonts/display.ttf'))).toString('base64');css=css.replace(/url\([^)]*display\.ttf[^)]*\)/g,`url("data:font/ttf;base64,${font}")`);
const assets={};for(const file of await readdir(path.join(root,'public/assets'))){if(!/\.(glb|json)$/.test(file)&&!/^car_thumb_[a-z]+\.png$/.test(file))continue;const b=await readFile(path.join(root,'public/assets',file));assets[file]=`data:${file.endsWith('.glb')?'model/gltf-binary':file.endsWith('.png')?'image/png':'application/json'};base64,${b.toString('base64')}`;}
for(const file of await readdir(path.join(root,'public/assets/map-previews'))){if(!file.endsWith('.png'))continue;assets['map-previews/'+file]='data:image/png;base64,'+(await readFile(path.join(root,'public/assets/map-previews',file))).toString('base64');}
html=html.replace(/<link[^>]*href=["']\.\/src\/style\.css["'][^>]*>/,()=>'<style>'+css+'</style>');
html=html.replace(/<script type="importmap">[\s\S]*?<\/script>/g,'');
html=html.replace(/<script type="module" src="\.\/src\/main\.js"><\/script>/,()=>`<script>window.__MALABAR_ASSETS__=${JSON.stringify(assets)};</script><script>${result.outputFiles[0].text.replace(/<\/script/gi,'<\\/script')}</script>`);
const ofl=await readFile(path.join(root,'public/assets/fonts/OFL.txt'),'utf8');
const threeLicense=await readFile(path.join(root,'public/vendor/THREE_LICENSE.txt'),'utf8');
html=html.replace('</head>',()=>`<!-- Three.js license\n${threeLicense.replace(/-->/g,'-- >')}\n-->\n<!-- Embedded font license\n${ofl.replace(/-->/g,'-- >')}\n-->\n</head>`);
if(html.includes('src="./src/main.js"'))throw new Error('Module entry replacement failed');
await writeFile(path.join(out,'malabar-hot-coast.html'),html);await writeFile(path.join(out,'game.bundle.js'),result.outputFiles[0].text);
console.log('Standalone HTML',Buffer.byteLength(html),'bytes; assets',Object.keys(assets).length);
