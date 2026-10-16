import {enemyTexture} from '../docs/routes/jigoku-2d/combat/duel-poses.mjs';
import {chromium} from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/combat',tmp='.tmp/duel-check';await fs.mkdir(`${tmp}/frames`,{recursive:true});
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const errors=[],failed=[],checks=[];
const guardRig=JSON.parse(await fs.readFile(`${out}/guard-rig.json`));
const state=p=>p.evaluate(()=>window.yariCombat.snapshot());
const click=(p,id)=>p.locator(id).evaluate(el=>el.click());
async function ready(p){p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400)failed.push(r.url());});await p.clock.install();await p.goto(`http://127.0.0.1:${server.address().port}/${out}/`);await p.waitForFunction(()=>window.yariCombat?.snapshot().ready);await p.clock.pauseAt(new Date(await p.evaluate(()=>Date.now())+2000));await p.clock.runFor(50);}
try{
 const p=await browser.newPage({viewport:{width:1280,height:1100}});await ready(p);
 assert.equal((await state(p)).duel.enabled,false);await click(p,'#duel');await p.clock.runFor(1100);
 const clip=await p.locator('#battle').boundingBox(),capture=[];let defended=false,attacked=false;
 for(let i=0;i<105;i++){
  const before=await state(p);
  if(!defended&&before.duel.stage==='windup'&&before.duel.age>=550){await p.evaluate(()=>document.activeElement.blur());await p.keyboard.press('l');defended=true;}
  if(defended&&!attacked&&before.duel.blocks===1&&before.duel.guard===0){await click(p,'#attack');attacked=true;}
  await p.clock.runFor(i%3===2?34:33);const row=await state(p),time=await p.evaluate(()=>Date.now());
  if(row.enemy.pose>=16){assert.ok(row.armOrder.upper>row.armOrder.body);assert.ok(row.armOrder.fore>row.armOrder.upper);assert.ok(row.armOrder.hand>row.armOrder.fore);}else{assert.ok(row.armOrder.upper<row.armOrder.body);assert.ok(row.armOrder.fore<row.armOrder.body);}
  const expected=enemyTexture(row.enemy.pose);assert.equal(row.enemyTexture,expected.key);assert.equal(row.enemyFrame,expected.frame);
  if(row.duel.guardPose!==null){
   assert.equal(row.texture,'guardBody');assert.equal(row.heroFrame,row.duel.guardPose);
   const w=row.guardWeapon,r=guardRig.weapon,p=w.pose,a=w.angle*Math.PI/180;
   assert.equal(w.visible,true);assert.equal(w.texture,'guardYari');assert.ok(w.order>w.bodyOrder);
   const map=(x,y)=>{const dx=(x/r.sourceSize[0]-w.originX)*w.width,dy=(y/r.sourceSize[1]-w.originY)*w.height;return {x:w.x+dx*Math.cos(a)-dy*Math.sin(a),y:w.y+dx*Math.sin(a)+dy*Math.cos(a)};};
   const butt=map(r.axisLeft,r.axisY),tip=map(r.axisRight,r.axisY);assert.ok(Math.abs(Math.hypot(tip.x-butt.x,tip.y-butt.y)-760)<1e-6);
   const scale=760/(r.axisRight-r.axisLeft),rear=map(r.axisLeft+180/scale,r.axisY),front=map(r.axisLeft+417/scale,r.axisY);
   assert.ok(Math.hypot(rear.x-p.palms[0].x,rear.y-p.palms[0].y)<1e-6);assert.ok(Math.hypot(front.x-p.palms[1].x,front.y-p.palms[1].y)<3);
   for(let j=0;j<2;j++){const h=w.hands[j];assert.equal(h.texture,'guardHands');assert.equal(h.frame,row.duel.guardPose*2+j);assert.equal(h.visible,true);assert.equal(h.width,64);assert.ok(h.order>w.order);assert.equal(h.x,p.palms[j].x);assert.equal(h.y,p.palms[j].y);}
  }else{assert.equal(row.guardWeapon.visible,false);assert.ok(row.guardWeapon.hands.every(h=>!h.visible));}
  for(const name of ['shoulder','elbow']){assert.ok(Math.abs(row.renderedArm[name].x-(row.target.x+(row.arm[name].x-576)*.6))<1e-6);assert.ok(Math.abs(row.renderedArm[name].y-(574+(row.arm[name].y-690)*.6))<1e-6);}
  assert.equal(row.body.x,row.target.x);assert.equal(row.body.y,574);assert.equal(row.enemyAngle,0);
  for(const [a,b,len] of [[row.arm.shoulder,row.arm.elbow,65],[row.arm.elbow,row.arm.wrist,75]])assert.ok(Math.abs(Math.hypot(a.x-b.x,a.y-b.y)-len)<1e-6);
  await p.screenshot({clip,path:`${tmp}/frames/${String(i).padStart(3,'0')}.png`});assert.equal(await p.evaluate(()=>Date.now()),time);
  if(i===25)await p.screenshot({path:`${out}/duel-desktop.jpg`,fullPage:true});
  capture.push({sample:i,time,guardWeapon:row.guardWeapon,texture:row.texture,heroFrame:row.heroFrame,enemyTexture:row.enemyTexture,enemyFrame:row.enemyFrame,armOrder:row.armOrder,renderedArm:row.renderedArm,body:row.body,duel:row.duel,phase:row.phase,frame:row.frame,hp:row.hp,enemy:row.enemy,arm:row.arm,weapon:row.weapon,hand:row.hand});
 }
 for(const pose of [16,17,18])assert.ok(capture.some(r=>r.enemy.pose===pose&&r.enemyTexture==='enemyDuel'));
 for(const pose of [0,1,2,3])assert.ok(capture.some(r=>r.duel.guardPose===pose&&r.texture==='guardBody'&&r.heroFrame===pose));
 assert.ok(defended&&attacked);assert.equal((await state(p)).duel.blocks,1);assert.equal((await state(p)).duel.playerHP,3);assert.equal((await state(p)).hp,2);
 checks.push('Keyboard L guards one telegraphed slash; counterattack damages enemy; all 3 authored enemy poses and four hero guard poses render with one 760 px spear, fixed 237 px grip anchors and foreground finger layers; actual shoulder/elbow sprites follow rigid sockets in 105 actual 30 Hz frames');
 await click(p,'#reset');await p.clock.runFor(1700);await click(p,'#guard');await p.clock.runFor(100);await click(p,'#pause');const held=(await state(p)).guardWeapon;await p.clock.runFor(1000);assert.deepEqual((await state(p)).guardWeapon,held);await click(p,'#pause');await click(p,'#reset');await p.clock.runFor(33);assert.equal((await state(p)).guardWeapon.visible,false);assert.ok((await state(p)).guardWeapon.hands.every(h=>!h.visible));checks.push('Pause freezes actual guard spear/finger transforms; reset hides all guard layers');
 await click(p,'#reset');await p.clock.runFor(1500);assert.equal((await state(p)).duel.stage,'windup');await click(p,'#pause');const paused=(await state(p)).duel;await p.clock.runFor(2000);assert.deepEqual((await state(p)).duel,paused);await click(p,'#pause');await p.clock.runFor(700);assert.equal((await state(p)).duel.playerHP,2);
 await p.clock.runFor(7000);assert.equal((await state(p)).duel.result,'defeat');assert.equal(await p.locator('#attack').isDisabled(),true);assert.equal(await p.locator('#guard').isDisabled(),true);assert.match(await p.locator('#enemy-cue').textContent(),/敗/);await click(p,'#reset');assert.equal((await state(p)).duel.playerHP,3);
 checks.push('Windup pause resumes without extra damage; three unblocked attacks end duel; reset restores health');
 await p.locator('#range').selectOption('far');await p.clock.runFor(2300);assert.equal((await state(p)).duel.playerHP,3);await p.locator('#target').selectOption('seal');assert.equal((await state(p)).duel.enabled,false);assert.equal(await p.locator('#duel').isDisabled(),true);
 checks.push('Far slash misses; seal practice disables enemy offense');
 await p.close();
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});await ready(mobile);assert.equal((await state(mobile)).hd,false);await mobile.locator('#feedback').uncheck();await mobile.locator('#duel').tap();await mobile.clock.runFor(1720);
 assert.equal((await state(mobile)).duel.stage,'windup');assert.equal(await mobile.locator('#enemy-cue').isVisible(),true);assert.match(await mobile.locator('#enemy-cue').textContent(),/蓄刀/);
 await mobile.screenshot({path:`${out}/duel-mobile.jpg`,fullPage:true});await mobile.locator('#guard').tap();await mobile.clock.runFor(33);assert.equal((await state(mobile)).texture,'guardBody');assert.equal((await state(mobile)).heroFrame,0);await mobile.clock.runFor(367);assert.equal((await state(mobile)).heroFrame,2);assert.equal((await state(mobile)).guardWeapon.visible,true);await mobile.screenshot({path:`${out}/duel-mobile-guard.jpg`,fullPage:true});assert.equal((await state(mobile)).duel.blocks,1);assert.equal((await state(mobile)).duel.playerHP,3);assert.equal((await state(mobile)).particles,0);assert.equal(await mobile.locator('#guard').isDisabled(),true);
 assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 checks.push('390 px touch: visible warning and successful block with feedback off/reduced motion; cooldown rejects repeat; no horizontal overflow');
 await mobile.close();assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 await fs.writeFile(`${out}/duel-capture.json`,JSON.stringify(capture,null,2)+'\n');await fs.writeFile(`${out}/duel-browser-check.json`,JSON.stringify({checks,pageErrors:errors,failedRequests:failed,frames:capture.length},null,2)+'\n');console.log(JSON.stringify({checks,errors,failed},null,2));
}finally{await browser.close();await new Promise(r=>server.close(r));}
