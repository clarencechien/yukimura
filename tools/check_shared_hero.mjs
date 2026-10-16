import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {thrustPose,sweepPose,sharedHeroPose} from '../docs/routes/jigoku-2d/combat/hero-rig.mjs';
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
 const s=new CombatState(track,()=>{},read('shared-sweep-track')),idle=sharedHeroPose(s,guard,rig);
 s.attack();assert.deepEqual(sharedHeroPose(s,guard,rig).transforms,idle.transforms);s.update(250);s.update(217);assert.equal(s.hits,1);
 const held=sharedHeroPose(s,guard,rig);s.update(40);assert.deepEqual(sharedHeroPose(s,guard,rig),held);s.paused=true;s.update(200);assert.deepEqual(sharedHeroPose(s,guard,rig),held);
 s.paused=false;s.reset();assert.deepEqual(sharedHeroPose(s,guard,rig),idle);
});
test('guard, ready and sweep share identical weapon transforms at handoff',()=>{
 const s=new CombatState(track,()=>{},read('shared-sweep-track'));s.startDuel();s.defend();s.duel.guard=50;
 const lowered=sharedHeroPose(s,guard,rig);s.duel.guard=0;const ready=sharedHeroPose(s,guard,rig);
 assert.ok(Math.hypot(lowered.weapon.tip.x-ready.weapon.tip.x,lowered.weapon.tip.y-ready.weapon.tip.y)<1e-6);
 s.attack('sweep');const sweep=sharedHeroPose(s,guard,rig);assert.equal(sweep.action,'sweep');assert.deepEqual(sweep.weapon.tip,ready.weapon.tip);assert.deepEqual(sweep.transforms,ready.transforms);
});

test('low sweep preserves limb lengths, wrist envelope and planted feet throughout continuous motion',()=>{
 for(let f=0;f<=310;f++){
  const p=sweepPose(f/10,guard,rig);
  for(const a of Object.values(p.arms)){
   assert.ok(Math.abs(distance(a.shoulder,a.elbow)-a.upper)<1e-6);assert.ok(Math.abs(distance(a.elbow,a.wrist)-a.fore)<1e-6);assert.ok(Math.abs(a.wristDeflection)<35);
  }
  assert.ok(p.weapon.registrationError<1e-6);assert.deepEqual(p.transforms.lower,{point:[0,0],angle:0});
  assert.ok(Math.abs(Math.hypot(p.weapon.tip.x-p.weapon.butt.x,p.weapon.tip.y-p.weapon.butt.y)-760)<1e-6);
 }
});
test('all low-sweep collision frames match the visible blade; existing hit window and duration retained',()=>{
 const t=read('shared-sweep-track');assert.equal(t.frames.length,32);assert.deepEqual(t.activeFrames,[9,10,11,12,13,14,15,16]);
 for(let i=0;i<32;i++)assert.deepEqual(sweepPose(i,guard,rig).weapon.tip,t.frames[i]);
 assert.deepEqual(sweepPose(0,guard,rig).transforms,sweepPose(31,guard,rig).transforms);
});
test('sweep key boundaries are continuous and pause, hitstop and reset preserve all shared parts',()=>{
 for(const f of [3,9,16,24]){
  const a=sweepPose(f-1e-5,guard,rig),b=sweepPose(f+1e-5,guard,rig);
  for(const name of Object.keys(a.transforms))assert.ok(distance(a.transforms[name].point,b.transforms[name].point)<1e-5);
 }
 const s=new CombatState(track,()=>{},read('shared-sweep-track'));s.attack('sweep');s.update(250);s.update(50);assert.equal(s.frame,9);assert.equal(s.hits,1);
 const hit=sharedHeroPose(s,guard,rig);s.update(40);assert.deepEqual(sharedHeroPose(s,guard,rig),hit);s.paused=true;s.update(200);assert.deepEqual(sharedHeroPose(s,guard,rig),hit);
 s.paused=false;s.reset();assert.deepEqual(sharedHeroPose(s,guard,rig).transforms,thrustPose(0,guard,rig).transforms);
});
