import {assertEnemyBody} from './enemy_body_browser_assertions.mjs';
import {assertDuelContact} from './duel_contact_browser_assertions.mjs';
import {assertHeroWeapon} from './shared_hero_browser_assertions.mjs';
import {enemyTexture} from '../docs/routes/jigoku-2d/combat/duel-poses.mjs';
import {chromium} from '@playwright/test';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd(),out='docs/routes/jigoku-2d/combat',tmp='.tmp/duel-check';await fs.mkdir(`${tmp}/frames`,{recursive:true});
const server=http.createServer(async(req,res)=>{try{let file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+'/'))throw Error('path');if((await fs.stat(file)).isDirectory())file=path.join(file,'index.html');res.setHeader('Content-Type',({'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp'})[path.extname(file)]||'application/octet-stream');res.end(await fs.readFile(file));}catch{res.statusCode=404;res.end('not found');}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const errors=[],failed=[],checks=[],requests=[];
const guardRig=JSON.parse(await fs.readFile(`${out}/guard-rig.json`));
const state=p=>p.evaluate(()=>window.yariCombat.snapshot());
const click=(p,id)=>p.locator(id).evaluate(el=>el.click());
async function ready(p){p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{requests.push(r.url());if(r.status()>=400)failed.push(r.url());});await p.clock.install();await p.goto(`http://127.0.0.1:${server.address().port}/${out}/`);await p.waitForFunction(()=>window.yariCombat?.snapshot().ready);await p.clock.pauseAt(new Date(await p.evaluate(()=>Date.now())+2000));await p.clock.runFor(50);}
try{
 const p=await browser.newPage({viewport:{width:1280,height:1100}});await ready(p);
 assert.equal((await state(p)).duel.enabled,false);await click(p,'#duel');await p.clock.runFor(1100);
 const clip=await p.locator('#battle').boundingBox(),capture=[];let defended=false,attacked=false;
 for(let i=0;i<105;i++){
  const before=await state(p);
  if(!defended&&before.duel.stage==='windup'&&before.duel.age>=550){await p.evaluate(()=>document.activeElement.blur());await p.keyboard.press('l');defended=true;}
  if(defended&&!attacked&&before.duel.blocks===1&&before.duel.guard===0){await click(p,'#attack');attacked=true;}
  await p.clock.runFor(i%3===2?34:33);const row=await state(p),time=await p.evaluate(()=>Date.now());
  assertEnemyBody(row);
  const expected=enemyTexture(row.enemyBodyPose?0:row.enemy.pose);assert.equal(row.enemyTexture,expected.key);assert.equal(row.enemyFrame,expected.frame);
  if(row.duel.guardPose!==null){assert.equal(row.heroArt.action,'guard');assert.equal(row.texture,'hero-lower');}
  assertHeroWeapon(row,guardRig);assertDuelContact(row,guardRig);
  for(const name of ['shoulder','elbow']){assert.ok(Math.abs(row.renderedArm[name].x-(row.target.x+(row.arm[name].x-576)*.6))<1e-6);assert.ok(Math.abs(row.renderedArm[name].y-(574+(row.arm[name].y-690)*.6))<1e-6);}
  assert.equal(row.body.x,row.target.x);assert.equal(row.body.y,574);assert.equal(row.enemyAngle,0);
  for(const [a,b,len] of [[row.arm.shoulder,row.arm.elbow,65],[row.arm.elbow,row.arm.wrist,75]])assert.ok(Math.abs(Math.hypot(a.x-b.x,a.y-b.y)-len)<1e-6);
  await p.screenshot({clip,path:`${tmp}/frames/${String(i).padStart(3,'0')}.png`});assert.equal(await p.evaluate(()=>Date.now()),time);
  if(i===25)await p.screenshot({path:`${out}/duel-desktop.jpg`,fullPage:true});
  capture.push({sample:i,time,enemyBodyPose:row.enemyBodyPose,enemyBodyParts:row.enemyBodyParts,legacyBodyVisible:row.legacyBodyVisible,targetKind:row.targetKind,target:row.target,contact:row.contact,lastClash:row.lastClash,heroArt:row.heroArt,heroParts:row.heroParts,heroWeapon:row.heroWeapon,texture:row.texture,heroFrame:row.heroFrame,enemyTexture:row.enemyTexture,enemyFrame:row.enemyFrame,armOrder:row.armOrder,renderedArm:row.renderedArm,body:row.body,duel:row.duel,phase:row.phase,frame:row.frame,hp:row.hp,enemy:row.enemy,arm:row.arm,weapon:row.weapon,hand:row.hand});
 }
 for(const pose of [16,17,18])assert.ok(capture.some(r=>r.enemy.pose===pose&&r.enemyBodyPose&&r.enemyBodyParts.torso.visible));
 for(const pose of [0,1,2,3])assert.ok(capture.some(r=>r.duel.guardPose===pose&&r.texture==='hero-lower'&&r.heroArt.action==='guard'));
 assert.ok(defended&&attacked);assert.equal((await state(p)).duel.blocks,1);assert.equal((await state(p)).duel.playerHP,3);assert.equal((await state(p)).hp,2);
 checks.push('Keyboard L guards one telegraphed slash; counterattack damages enemy; all 3 enemy action stages use the same rigid torso and fixed lower body; continuous shared hero guard renders with one 760 px spear, fixed 237 px grip anchors and foreground finger layers; actual shoulder/elbow sprites follow rigid sockets in 105 actual 30 Hz frames');
 assert.ok(capture.some(r=>r.contact?.weight===1&&r.duel.blocks===1));assert.ok(capture.some(r=>r.contact?.weight>0&&r.contact.weight<1&&r.duel.blocks===1));
 checks.push('Actual rendered blade texture marker meets actual spear shaft during block; fixed blade dimensions and arm lengths; visible deflection releases contact');
 await click(p,'#reset');await p.clock.runFor(1700);await click(p,'#guard');await p.clock.runFor(380);await click(p,'#pause');const pausedClash=await state(p);assert.equal(pausedClash.contact.weight,1);assertDuelContact(pausedClash,guardRig);await p.clock.runFor(1000);const afterClash=await state(p);for(const name of ['heroWeapon','contact','lastClash','arm','weapon','enemyBodyParts'])assert.deepEqual(afterClash[name],pausedClash[name]);await click(p,'#pause');await click(p,'#reset');await p.clock.runFor(33);assert.equal((await state(p)).heroArt.action,'idle');assert.equal((await state(p)).texture,'hero-lower');assertHeroWeapon(await state(p),guardRig);checks.push('Pause freezes both contacting weapons, arms and clash point; reset returns to the shared lower-ready pose');
 await click(p,'#reset');await p.clock.runFor(1500);assert.equal((await state(p)).duel.stage,'windup');await click(p,'#pause');const paused=(await state(p)).duel;await p.clock.runFor(2000);assert.deepEqual((await state(p)).duel,paused);await click(p,'#pause');await p.clock.runFor(700);assert.equal((await state(p)).duel.playerHP,2);
 await p.clock.runFor(7000);assert.equal((await state(p)).duel.result,'defeat');assert.equal(await p.locator('#attack').isDisabled(),true);assert.equal(await p.locator('#guard').isDisabled(),true);assert.match(await p.locator('#enemy-cue').textContent(),/敗/);await click(p,'#reset');assert.equal((await state(p)).duel.playerHP,3);
 checks.push('Windup pause resumes without extra damage; three unblocked attacks end duel; reset restores health');
 await p.locator('#range').selectOption('far');await p.clock.runFor(2300);assert.equal((await state(p)).duel.playerHP,3);await p.locator('#target').selectOption('seal');assert.equal((await state(p)).duel.enabled,false);assert.equal(await p.locator('#duel').isDisabled(),true);
 checks.push('Far slash misses; seal practice disables enemy offense');
 // Capture a thrust that actually interrupts windup, including hitstop and return.
 await p.locator('#target').selectOption('warrior');await p.locator('#range').selectOption('near');await click(p,'#duel');await p.locator('#feedback').uncheck();await p.clock.runFor(1300);await click(p,'#attack');
 const recoil=[];await fs.mkdir('.tmp/enemy-recoil/frames',{recursive:true});
 for(let i=0;i<60;i++){
  await p.clock.runFor(i%3===2?34:33);const row=await state(p),time=await p.evaluate(()=>Date.now());
  assertEnemyBody(row);assertHeroWeapon(row,guardRig);
  if(row.enemy.bodyReaction){assert.equal(row.enemy.bodyReaction.from.intent,'windup');assert.equal(row.enemyFrame,0);assert.equal(row.legacyBodyVisible,false);assert.equal(row.weapon.held,true);assert.equal(row.hand.state,'grip');}
  for(const [a,b,len] of [[row.arm.shoulder,row.arm.elbow,65],[row.arm.elbow,row.arm.wrist,75]])assert.ok(Math.abs(Math.hypot(a.x-b.x,a.y-b.y)-len)<1e-6);
  await p.screenshot({clip,path:`.tmp/enemy-recoil/frames/${String(i).padStart(3,'0')}.png`});assert.equal(await p.evaluate(()=>Date.now()),time);
  recoil.push({sample:i,time,phase:row.phase,frame:row.frame,hp:row.hp,freeze:row.freeze,enemyAge:row.enemyAge,enemy:row.enemy,duel:row.duel,enemyBodyPose:row.enemyBodyPose,enemyBodyParts:row.enemyBodyParts,legacyBodyVisible:row.legacyBodyVisible,renderedArm:row.renderedArm,arm:row.arm,weapon:row.weapon,hand:row.hand});
 }
 const reactions=recoil.filter(r=>r.enemy.bodyReaction);assert.ok(reactions.length>=10);assert.ok(reactions.some(r=>r.enemyAge>300));assert.ok(reactions.some(r=>r.freeze>0));
 const frozen=reactions.filter(r=>r.freeze>0);assert.ok(frozen.length>=1);for(const row of frozen)assert.deepEqual(row.enemyBodyParts,frozen[0].enemyBodyParts);
 assert.equal(recoil.at(-1).enemy.phase,'guard');assert.equal(recoil.at(-1).hp,2);assert.equal(recoil.at(-1).duel.playerHP,3);assert.ok(recoil.some(r=>r.hp===2&&r.enemy.phase==='guard'&&r.duel.stage==='recovery'&&r.enemyBodyPose.angle===0));
 await fs.writeFile(`${out}/enemy-recoil-capture.json`,JSON.stringify(recoil,null,2)+'\n');
 checks.push('60 actual 30 Hz frames: thrust interrupts windup, hitstop holds the same torso, rigid chest/arm recoil and return to ready; no effects required, no player damage');
 // A 30 Hz screenshot sample need not contain two rendered hitstop frames.
 // Verify the hold separately with a bounded 10 ms input clock, then 16 ms.
 await click(p,'#reset');await p.clock.runFor(1300);await click(p,'#attack');let firstHit;
 for(let i=0;i<70;i++){await p.clock.runFor(10);const r=await state(p);if(r.hp===2){firstHit=r;break;}}
 assert.ok(firstHit&&firstHit.freeze>20);assert.equal(firstHit.enemyAge,0);await p.clock.runFor(16);const duringHit=await state(p);assert.equal(duringHit.enemyAge,0);for(const key of ['enemyBodyParts','arm','weapon'])assert.deepEqual(duringHit[key],firstHit[key]);checks.push('Separate fine clock check: actual chest, arm and weapon remain identical across rendered hitstop frames');
 await p.close();
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});await ready(mobile);assert.equal((await state(mobile)).hd,false);await mobile.locator('#feedback').uncheck();await mobile.locator('#duel').tap();await mobile.clock.runFor(1720);
 assert.equal((await state(mobile)).duel.stage,'windup');assert.equal(await mobile.locator('#enemy-cue').isVisible(),true);assert.match(await mobile.locator('#enemy-cue').textContent(),/蓄刀/);
 await mobile.screenshot({path:`${out}/duel-mobile.jpg`,fullPage:true});await mobile.locator('#guard').tap();await mobile.clock.runFor(33);assert.equal((await state(mobile)).texture,'hero-lower');assert.equal((await state(mobile)).heroArt.action,'guard');assertHeroWeapon(await state(mobile),guardRig);await mobile.clock.runFor(337);assert.equal((await state(mobile)).heroArt.action,'guard');assert.ok((await state(mobile)).heroArt.guard.recoil>0);assertHeroWeapon(await state(mobile),guardRig);assert.equal((await state(mobile)).heroWeapon.visible,true);assertDuelContact(await state(mobile),guardRig);assertEnemyBody(await state(mobile));assert.equal((await state(mobile)).contact.weight,1);await mobile.screenshot({path:`${out}/duel-mobile-guard.jpg`,fullPage:true});assert.equal((await state(mobile)).duel.blocks,1);assert.equal((await state(mobile)).duel.playerHP,3);assert.equal((await state(mobile)).particles,0);assert.equal(await mobile.locator('#guard').isDisabled(),true);
 assert.equal(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 checks.push('390 px touch: visible warning and successful block with feedback off/reduced motion; cooldown rejects repeat; no horizontal overflow');
 await click(mobile,'#reset');await mobile.clock.runFor(1300);await mobile.locator('#attack').tap();await mobile.clock.runFor(650);const mobileHit=await state(mobile);assertEnemyBody(mobileHit);assert.ok(mobileHit.enemy.bodyReaction);assert.equal(mobileHit.hp,2);assert.equal(mobileHit.particles,0);await mobile.screenshot({path:`${out}/enemy-recoil-mobile.jpg`,fullPage:true});await mobile.locator('#pause').tap();const held=(await state(mobile)).enemyBodyParts;await mobile.clock.runFor(800);assert.deepEqual((await state(mobile)).enemyBodyParts,held);checks.push('390 px touch nonfatal thrust uses the same chest without effects; pause holds actual rendered body parts');
 await mobile.close();assert.ok(!requests.some(u=>/enemy-duel(-hd)?\.webp$/.test(u)));checks.push('No full-body enemy duel atlas requested; actual rigid chest transform carries shoulder socket and lower body stays planted on desktop/mobile');assert.ok(!requests.some(u=>/guard-(body|hands)(-hd)?\.webp$/.test(u)));checks.push('No legacy guard body or finger atlas requested; guard, ready and counterattack share the same fourteen parts');assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 await fs.writeFile(`${out}/duel-capture.json`,JSON.stringify(capture,null,2)+'\n');await fs.writeFile(`${out}/duel-browser-check.json`,JSON.stringify({checks,pageErrors:errors,failedRequests:failed,frames:capture.length},null,2)+'\n');console.log(JSON.stringify({checks,errors,failed},null,2));
}finally{await browser.close();await new Promise(r=>server.close(r));}
