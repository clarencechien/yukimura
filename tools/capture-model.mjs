/** Capture the actual runtime GLB; run Vite first. No image-generation step. */
import {chromium} from '@playwright/test';
import {existsSync} from 'node:fs';
const url=process.argv[2]||'http://127.0.0.1:5173/tools/model-preview.html';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1200,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 await page.goto(url);await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
 await page.evaluate(async()=>{const p=window.modelPreview;await p.scene.whenReadyAsync();p.loaded.animationGroups.forEach(g=>g.stop());});
 // Let the postprocess/shadow shader variants render before taking stills.
 await page.waitForTimeout(2000);
 await page.screenshot({path:'docs/art/hero-runtime-front.png'});
 await page.evaluate(()=>{window.modelPreview.camera.alpha+=Math.PI;});
 await page.waitForTimeout(500);await page.screenshot({path:'docs/art/hero-runtime-back.png'});
 await page.evaluate(()=>{window.modelPreview.camera.alpha=Math.PI;});
 await page.waitForTimeout(500);await page.screenshot({path:'docs/art/hero-runtime-side.png'});
 await page.evaluate(()=>{const p=window.modelPreview;p.camera.alpha=1.20;p.camera.radius=2.45;p.camera.target.y=2.05;});
 await page.waitForTimeout(500);await page.screenshot({path:'docs/art/hero-runtime-detail.png'});
 await page.evaluate(()=>{const p=window.modelPreview;p.camera.radius=4.8;p.camera.target.y=1.38;p.play('slash');const g=p.loaded.animationGroups.find(g=>g.name==='slash');g.pause();g.goToFrame(g.from+(g.to-g.from)*.34);});
 await page.waitForTimeout(500);await page.screenshot({path:'docs/art/hero-runtime-slash.png'});
 await page.evaluate(()=>{const p=window.modelPreview;p.play('idle');const g=p.loaded.animationGroups.find(g=>g.name==='idle');g.pause();g.goToFrame(g.from);p.camera.detachPostProcess(p.ink);p.camera.radius=2.45;p.camera.target.y=2.05;document.querySelector('aside p').textContent='實際 GLB · PBR 材質 · 無墨線／紙色濾鏡';});
 await page.waitForTimeout(500);await page.screenshot({path:'docs/art/hero-runtime-pbr.png'});
 if(errors.length)throw new Error(errors.join('\n'));
 console.log('Captured front, back, side, detail, slash and unfiltered PBR from the actual Babylon.js GLB.');
}finally{await browser.close();}
