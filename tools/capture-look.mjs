/** Current look at the same cameras as the v10 baseline; genuine engine output. */
import {chromium} from '@playwright/test';
import {existsSync,writeFileSync} from 'node:fs';
const base=process.argv[2]||'http://127.0.0.1:5180';
const browser=await chromium.launch({executablePath:existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`)});
 await page.goto(base+'/?test');await page.waitForFunction(()=>!document.querySelector('#start').disabled,{},{timeout:60000});await page.click('#start');await page.waitForTimeout(1800);
 await page.evaluate(()=>window.__sanadaTest.inspectEnvironment(0,true));await page.addStyleTag({content:'#app{visibility:hidden!important}'});await page.waitForTimeout(600);
 await page.screenshot({path:'docs/screenshots/lighting-after.png'});
 writeFileSync('docs/screenshots/lighting-budget.json',JSON.stringify(await page.evaluate(()=>window.__sanada.look),null,2)+'\n');
 await page.goto(base+'/tools/model-preview.html');await page.waitForFunction(()=>window.modelPreview?.ready,{},{timeout:60000});
 await page.evaluate(async()=>{const p=window.modelPreview;await p.scene.whenReadyAsync();p.loaded.animationGroups.forEach(g=>{g.pause();g.goToFrame(0)});p.camera.alpha=1.45;p.camera.beta=1.38;p.camera.radius=3.3;p.camera.target.y=1.6;});
 await page.waitForTimeout(800);await page.screenshot({path:'docs/screenshots/material-after.png'});
 if(errors.length)throw Error(errors.join('\n'));console.log('Saved material/lighting views and actual render-target dimensions.');
}finally{await browser.close();}
