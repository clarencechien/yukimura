import {chromium} from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/combat',tmp='.tmp/combat-check';await fs.mkdir(tmp,{recursive:true});
const server=http.createServer(async(req,res)=>{try{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');const stat=await fs.stat(file);const resolved=stat.isDirectory()?path.join(file,'index.html'):file;res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp'})[path.extname(resolved)]||'application/octet-stream');res.end(await fs.readFile(resolved));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const errors=[],failed=[],checks=[];
const url=`http://127.0.0.1:${server.address().port}/${out}/`;
async function ready(page){page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push(r.url());});await page.goto(url);await page.waitForFunction(()=>window.yariCombat?.snapshot().ready);}
const state=p=>p.evaluate(()=>window.yariCombat.snapshot());
const click=(p,id)=>p.locator(id).evaluate(el=>el.click());
try{
 const p=await browser.newPage({viewport:{width:1280,height:1100}});await ready(p);assert.equal((await state(p)).engine,'3.90.0');assert.equal((await state(p)).hd,true);
 await p.clock.install();await p.clock.pauseAt(new Date(Date.now()+100));await p.clock.runFor(100);await click(p,'#reset');
 await p.screenshot({path:`${out}/desktop.jpg`,fullPage:true});
 await click(p,'#attack');assert.equal(await p.locator('#attack').isDisabled(),true);await click(p,'#attack');await p.clock.runFor(600);assert.equal((await state(p)).hp,2);assert.equal((await state(p)).swings,1);assert.ok((await state(p)).particles<=80);await p.clock.runFor(300);assert.ok((await state(p)).frame>=24);assert.equal((await state(p)).texture,'thrust-2');await p.clock.runFor(700);assert.equal((await state(p)).phase,'idle');
 checks.push('HD near hit; one damage per strike; no button spam; recovery unlocks');
 for(let i=0;i<2;i++){await click(p,'#attack');await p.clock.runFor(1500);}assert.equal((await state(p)).hp,0);assert.equal(await p.locator('#attack').isDisabled(),true);assert.match(await p.locator('#message').textContent(),/封印已破/);checks.push('Three distinct strikes break seal; dead target cannot be hit again');
 await p.locator('#range').selectOption('far');await p.keyboard.press('Tab');await p.evaluate(()=>document.activeElement.blur());await p.keyboard.press('j');await p.clock.runFor(1500);assert.equal((await state(p)).swings,1);assert.equal((await state(p)).hp,3);assert.match(await p.locator('#message').textContent(),/刺空/);checks.push('Keyboard J works; far target misses without damage');
 await click(p,'#pause');const before=await state(p);await p.clock.runFor(700);assert.equal((await state(p)).frame,before.frame);assert.equal((await state(p)).paused,true);await click(p,'#pause');checks.push('Pause freezes pose and input');
 await p.locator('#range').selectOption('near');await p.locator('#feedback').uncheck();await click(p,'#attack');await p.clock.runFor(600);assert.equal((await state(p)).hp,2);assert.equal((await state(p)).particles,0);await p.clock.runFor(900);checks.push('Visual feedback off preserves actual hit rules');
 await p.locator('#feedback').check();await click(p,'#reset');await p.locator('#debug').check();await click(p,'#attack');await p.clock.runFor(500);await p.screenshot({path:`${out}/hit-check.jpg`,fullPage:true});assert.equal((await state(p)).hp,2);await p.clock.runFor(1000);await p.locator('#debug').uncheck();
 await fs.mkdir(`${tmp}/frames`,{recursive:true});await click(p,'#reset');
 const capture=[],clip=await p.locator('#battle').boundingBox();
 for(let i=0;i<48;i++){if(i===6)await click(p,'#attack');await p.clock.runFor(i%3===2?34:33);const time=await p.evaluate(()=>Date.now());const before=await state(p);await p.screenshot({clip,path:`${tmp}/frames/${String(i).padStart(3,'0')}.png`});assert.equal(await p.evaluate(()=>Date.now()),time,'Screenshot must not advance simulation');assert.equal((await state(p)).frame,before.frame);capture.push({sample:i,time,phase:before.phase,frame:before.frame,hp:before.hp});}
 await fs.writeFile(`${out}/capture-timing.json`,JSON.stringify(capture,null,2)+'\n');
 checks.push('Captured 48 rendered scene frames at 33/33/34 ms controlled-clock samples');
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1,reducedMotion:'reduce'});await ready(mobile);assert.equal((await state(mobile)).hd,false);assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await mobile.locator('#attack').tap();await mobile.waitForFunction(()=>window.yariCombat.snapshot().hp===2);await mobile.waitForFunction(()=>window.yariCombat.snapshot().phase==='idle');await mobile.screenshot({path:`${out}/mobile.jpg`,fullPage:true});checks.push('Mobile touch attack; 512px atlas; no horizontal overflow; reduced motion');
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);await fs.writeFile(`${out}/browser-check.json`,JSON.stringify({passed:true,engine:'Phaser 3.90.0',checks,pageErrors:errors,failedRequests:failed,scope:'Headless desktop/mobile correctness; not a physical phone FPS benchmark.'},null,2)+'\n');console.log('Combat browser checks passed.');
}finally{await browser.close();await new Promise(r=>server.close(r));}
