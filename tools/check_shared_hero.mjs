import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {thrustPose,sharedHeroPose} from '../docs/routes/jigoku-2d/combat/hero-rig.mjs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
const read=n=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/combat/${n}.json`));
const guard=read('guard-rig'),rig=read('thrust-rig'),track=read('shared-spear-track');
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
test('continuous short-thrust envelope stays reachable, fixed-length and within projected wrist limits',()=>{
 for(let f=0;f<=350;f++){
  const p=thrustPose(f/10,guard,rig);
  for(const [side,a] of Object.entries(p.arms)){
   assert.ok(Math.abs(distance(a.shoulder,a.elbow)-a.upper)<1e-6);assert.ok(Math.abs(distance(a.elbow,a.wrist)-a.fore)<1e-6);
   assert.ok(Math.abs(a.wristDeflection)<35,side+' projected wrist angle');
  }
  assert.ok(Math.abs(Math.hypot(p.weapon.tip.x-p.weapon.butt.x,p.weapon.tip.y-p.weapon.butt.y)-760)<1e-6);
  assert.ok(p.weapon.registrationError<1e-6);assert.deepEqual(p.transforms.lower,{point:[0,0],angle:0});
 }
});
test('collision track equals the shared rendered spear endpoint throughout all 36 frames',()=>{
 assert.equal(track.frames.length,36);assert.deepEqual(track.activeFrames,[14,15]);
 for(let f=0;f<36;f++)assert.deepEqual(thrustPose(f,guard,rig).weapon.tip,track.frames[f]);
 const a=thrustPose(0,guard,rig),b=thrustPose(35,guard,rig);assert.deepEqual(a.transforms,b.transforms);assert.deepEqual(a.weapon.tip,b.weapon.tip);
});
test('idle and attack boundaries share rig transforms; hitstop, pause and reset freeze/restore the whole rig',()=>{
 const s=new CombatState(track,()=>{},read('sweep-track')),idle=sharedHeroPose(s,guard,rig);
 s.attack();assert.deepEqual(sharedHeroPose(s,guard,rig).transforms,idle.transforms);s.update(250);s.update(217);assert.equal(s.hits,1);
 const held=sharedHeroPose(s,guard,rig);s.update(40);assert.deepEqual(sharedHeroPose(s,guard,rig),held);s.paused=true;s.update(200);assert.deepEqual(sharedHeroPose(s,guard,rig),held);
 s.paused=false;s.reset();assert.deepEqual(sharedHeroPose(s,guard,rig),idle);
});
test('guard hands off to the same spear and sweep hides every shared hero layer',()=>{
 const s=new CombatState(track,()=>{},read('sweep-track'));s.startDuel();s.defend();s.duel.guard=50;
 const lowered=sharedHeroPose(s,guard,rig);s.duel.guard=0;const ready=sharedHeroPose(s,guard,rig);
 assert.ok(Math.hypot(lowered.weapon.tip.x-ready.weapon.tip.x,lowered.weapon.tip.y-ready.weapon.tip.y)<1e-6);
 s.attack('sweep');assert.equal(sharedHeroPose(s,guard,rig),null);
});
