import {chromium} from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {assertHeroWeapon} from './shared_hero_browser_assertions.mjs';
const root=process.cwd(),out='docs/routes/jigoku-2d/combat',tmp='.tmp/shared-sweep-check';await fs.mkdir(`${tmp}/frames`,{recursive:true});
const guard=JSON.parse(await fs.readFile(`${out}/guard-rig.json`));
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.mjs':'text/javascript','.js':'text/javascript','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const errors=[],requests=[],capture=[],checks=[];
const state=p=>p.evaluate(()=>window.yariCombat.snapshot()),click=(p,id)=>p.locator(id).evaluate(el=>el.click());
async function ready(p){p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});p.on('response',r=>{if(r.status()>=400)errors.push(r.url());requests.push(r.url());});await p.clock.install();await p.goto(`http://127.0.0.1:${server.address().port}/${out}/`);await p.waitForFunction(()=>window.yariCombat?.snapshot().ready);await p.clock.pauseAt(new Date(await p.evaluate(()=>Date.now())+2000));await p.clock.runFor(50);assert.equal(await p.locator('html').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(16, 20, 23)');}
try{
 const p=await browser.newPage({viewport:{width:1280,height:1100}});await ready(p);await click(p,'#reset');await p.clock.runFor(33);assertHeroWeapon(await state(p),guard);await p.screenshot({path:`${out}/shared-sweep-idle.jpg`,fullPage:true});const clip=await p.locator('#battle').boundingBox();let contact=false;
 for(let i=0;i<60;i++){
  if(i===6)await click(p,'#sweep');await p.clock.runFor(i%3===2?34:33);const row=await state(p),time=await p.evaluate(()=>Date.now());assertHeroWeapon(row,guard);
  await p.screenshot({clip,path:`${tmp}/frames/${String(i).padStart(3,'0')}.png`});assert.equal(await p.evaluate(()=>Date.now()),time);
  if(!contact&&row.frame===9&&row.phase==='attack'){await p.screenshot({path:`${out}/shared-sweep-contact.jpg`,fullPage:true});contact=true;}
  capture.push({sample:i,time,...row});
 }
 assert.ok(contact);assert.equal((await state(p)).hits,1);assert.equal((await state(p)).hp,2);assert.equal((await state(p)).phase,'idle');
 checks.push('60 real desktop low-sweep frames: fixed arm/leg lengths, connected hip/knee/ankle sockets, source-size rigid layers, palm/shaft registration, visible spear tip equals collision track, feet fixed');
 await click(p,'#reset');await click(p,'#sweep');await p.clock.runFor(350);await click(p,'#pause');const held=await state(p);await p.clock.runFor(500);const paused=await state(p);assert.deepEqual(paused.heroParts,held.heroParts);assert.deepEqual(paused.heroWeapon,held.heroWeapon);await click(p,'#pause');await click(p,'#reset');await p.clock.runFor(33);assert.equal((await state(p)).heroArt.action,'idle');
 checks.push('Pause freezes torso, hip, all arm/leg joints, feet, hands and spear; reset restores ready stance');await p.close();
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});await ready(mobile);assert.equal((await state(mobile)).hd,false);await mobile.locator('#feedback').uncheck();await mobile.locator('#sweep').tap();let mobileContact=false;
 for(let i=0;i<45;i++){
  await mobile.clock.runFor(i%3===2?34:33);const row=await state(mobile);assertHeroWeapon(row,guard);
  if(row.frame===9&&row.phase==='attack'&&!mobileContact){await mobile.screenshot({path:`${out}/shared-sweep-mobile.jpg`,fullPage:true});mobileContact=true;}
 }
 assert.ok(mobileContact);assert.equal((await state(mobile)).hits,1);assert.equal((await state(mobile)).particles,0);assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 checks.push('390 px touch low sweep: same rendered arm, hand and blade checks; one hit; feedback off; no horizontal overflow');
 await mobile.close();assert.ok(!requests.some(u=>u.includes('/yari-rigid/')||/\/sweep(?:-hd|-boundary(?:-hd)?)?\.webp$/.test(u)));assert.deepEqual(errors,[]);checks.push('No request for old idle/thrust/sweep atlases or sweep boundary cells; zero page errors and failed asset requests');
 await fs.writeFile(`${out}/shared-sweep-capture.json`,JSON.stringify(capture,null,2)+'\n');await fs.writeFile(`${out}/shared-sweep-browser-check.json`,JSON.stringify({passed:true,checks,frames:capture.length,errors},null,2)+'\n');console.log(checks);
}finally{await browser.close();await new Promise(r=>server.close(r));}
