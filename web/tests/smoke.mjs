import { chromium } from '@playwright/test';
import {mkdir} from 'node:fs/promises';
await mkdir('../../renders/browser',{recursive:true});
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-dev-shm-usage']});
const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
page.on('pageerror',e=>console.log('PAGEERROR',e.message));page.on('console',m=>{if(m.type()==='error'||m.type()==='warn')console.log(m.type(),m.text());});
await page.goto('http://127.0.0.1:8080',{waitUntil:'networkidle'});
await page.waitForFunction(()=>window.__MALABAR__?.ready||window.__MALABAR__?.error,{timeout:120000});
await page.waitForTimeout(2500);console.log('INITIAL',JSON.stringify(await page.evaluate(()=>({ready:window.__MALABAR__.ready,error:window.__MALABAR__.error,snapshot:window.__MALABAR__.snapshot()}))));
await page.screenshot({path:'../renders/browser/menu-desktop.png'});
if(await page.evaluate(()=>window.__MALABAR__.ready)){
 await page.locator('#home-ride').click();await page.waitForTimeout(4000);await page.keyboard.down('KeyW');await page.waitForTimeout(5000);await page.keyboard.up('KeyW');
 console.log('DRIVE',JSON.stringify(await page.evaluate(()=>window.__MALABAR__.snapshot())));await page.screenshot({path:'../renders/browser/first-drive.png'});
}
await browser.close();
