import {assertEnemyBody} from './enemy_body_browser_assertions.mjs';
import {assertHeroWeapon} from './shared_hero_browser_assertions.mjs';
import {chromium} from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/combat',tmp='.tmp/fatal-mobile';await fs.mkdir(tmp,{recursive:true});
const server=http.createServer(async(req,res)=>{try{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');const stat=await fs.stat(file);const resolved=stat.isDirectory()?path.join(file,'index.html'):file;res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp'})[path.extname(resolved)]||'application/octet-stream');res.end(await fs.readFile(resolved));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const errors=[],failed=[],checks=[];
const guardRig=JSON.parse(await fs.readFile(`${out}/guard-rig.json`));
const url=`http://127.0.0.1:${server.address().port}/${out}/`;
async function ready(page){page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)failed.push(r.url());});await page.goto(url);await page.waitForFunction(()=>window.yariCombat?.snapshot().ready);}
const state=p=>p.evaluate(()=>window.yariCombat.snapshot());
const click=(p,id)=>p.locator(id).evaluate(el=>el.click());
try{
 const p=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1,reducedMotion:'reduce'});
 await p.clock.install();await ready(p);await p.clock.pauseAt(new Date(await p.evaluate(()=>Date.now())+2000));await p.clock.runFor(100);await p.locator('#feedback').uncheck();
 for(const kind of ['thrust','sweep']){
  await click(p,'#reset');for(let i=0;i<2;i++){await p.locator('#attack').tap();await p.clock.runFor(1500);}
  await p.locator(kind==='thrust'?'#attack':'#sweep').tap();
  let row;for(let i=0;i<80;i++){await p.clock.runFor(10);row=await state(p);if(row.hp===0)break;}
  assert.equal(row.hp,0);assert.ok(row.enemyBodyPose);assert.equal(row.enemy.bodyReaction.fatal,true);assertEnemyBody(row);assertHeroWeapon(row,guardRig);
  await p.clock.runFor(100);await click(p,'#pause');const held=await state(p);assert.ok(held.enemyBodyPose.root.y>0);assertEnemyBody(held);await p.clock.runFor(500);assert.deepEqual((await state(p)).enemyBodyParts,held.enemyBodyParts);await p.screenshot({path:`${out}/enemy-fatal-${kind}-mobile.jpg`,fullPage:true});
  await click(p,'#pause');await p.clock.runFor(200);row=await state(p);assert.equal(row.enemyBodyPose,null);assertEnemyBody(row);
  await p.clock.runFor(1600);row=await state(p);assert.equal(row.weapon.landed,true);assert.equal(row.weapon.alpha,0);assert.equal(row.enemy.phase,'gone');
  checks.push(`${kind}: real touch, mobile textures, shared fatal impact/load, pause, authored handoff, release/landing/fade`);
 }
 await click(p,'#reset');await p.clock.runFor(33);assertEnemyBody(await state(p));assert.equal((await state(p)).hp,3);assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 await fs.writeFile(`${out}/enemy-fatal-mobile-check.json`,JSON.stringify({passed:true,checks,pageErrors:errors,failedRequests:failed,scope:'390 px touch emulation and actual Phaser transforms, not physical phone performance.'},null,2)+'\n');console.log('Fatal mobile browser checks passed.');
}finally{await browser.close();await new Promise(r=>server.close(r));}
