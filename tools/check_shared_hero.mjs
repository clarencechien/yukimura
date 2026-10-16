import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {thrustPose,sweepPose,sharedHeroPose,sharedGuardPose} from '../docs/routes/jigoku-2d/combat/hero-rig.mjs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
const read=n=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/combat/${n}.json`));
const guard=read('guard-rig'),rig=read('thrust-rig'),track=read('shared-spear-track');
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]);
function assertPlantedLegs(p){
 for(const [side,j] of Object.entries(rig.legs)){
  const leg=p.legs[side];
  assert.ok(Math.abs(distance(leg.hip,leg.knee)-distance(j.hip,j.knee))<1e-6);
  assert.ok(Math.abs(distance(leg.knee,leg.ankle)-distance(j.knee,j.ankle))<1e-6);
  assert.deepEqual(leg.ankle,j.ankle);
  assert.deepEqual(p.transforms[side+'Foot'],{point:j.ankle,angle:0});
  assert.ok(distance(leg.hip,[j.hip[0]+p.root[0],j.hip[1]+p.root[1]])<1e-6);
  const v=[leg.ankle[0]-leg.hip[0],leg.ankle[1]-leg.hip[1]],k=[leg.knee[0]-leg.hip[0],leg.knee[1]-leg.hip[1]];
  assert.equal(Math.sign(v[0]*k[1]-v[1]*k[0]),j.bend,'knee must retain its bend branch');
 }
 assert.deepEqual(p.transforms.lower.point,p.transforms.torso.point);
}
test('continuous short-thrust envelope stays reachable, fixed-length and within projected wrist limits',()=>{
 for(let f=0;f<=350;f++){
  const p=thrustPose(f/10,guard,rig);
  for(const [side,a] of Object.entries(p.arms)){
   assert.ok(Math.abs(distance(a.shoulder,a.elbow)-a.upper)<1e-6);assert.ok(Math.abs(distance(a.elbow,a.wrist)-a.fore)<1e-6);
   assert.ok(Math.abs(a.wristDeflection)<35,side+' projected wrist angle');
  }
  assert.ok(Math.abs(Math.hypot(p.weapon.tip.x-p.weapon.butt.x,p.weapon.tip.y-p.weapon.butt.y)-760)<1e-6);
  assert.ok(p.weapon.registrationError<1e-6);assertPlantedLegs(p);
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
 const s=new CombatState(track,()=>{},read('shared-sweep-track'));s.startDuel();s.defend();s.duel.guard=0;
 const lowered=sharedGuardPose(580,null,guard,rig);s.duel.guard=0;const ready=sharedHeroPose(s,guard,rig);
 assert.ok(Math.hypot(lowered.weapon.tip.x-ready.weapon.tip.x,lowered.weapon.tip.y-ready.weapon.tip.y)<1e-6);
 s.attack('sweep');const sweep=sharedHeroPose(s,guard,rig);assert.equal(sweep.action,'sweep');assert.deepEqual(sweep.weapon.tip,ready.weapon.tip);assert.deepEqual(sweep.transforms,ready.transforms);
});

test('low sweep preserves limb lengths, wrist envelope and planted feet throughout continuous motion',()=>{
 for(let f=0;f<=310;f++){
  const p=sweepPose(f/10,guard,rig);
  for(const a of Object.values(p.arms)){
   assert.ok(Math.abs(distance(a.shoulder,a.elbow)-a.upper)<1e-6);assert.ok(Math.abs(distance(a.elbow,a.wrist)-a.fore)<1e-6);assert.ok(Math.abs(a.wristDeflection)<35);
  }
  assert.ok(p.weapon.registrationError<1e-6);assertPlantedLegs(p);
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

test('pelvis loads before contact, knees respond, and neither leg is stretched to move the torso',()=>{
 const ready=sweepPose(0,guard,rig),load=sweepPose(3,guard,rig),contact=sweepPose(9,guard,rig);
 assert.ok(load.root[1]>0);assert.ok(contact.root[1]>load.root[1]);
 for(const side of ['rear','front'])assert.ok(distance(contact.legs[side].knee,ready.legs[side].knee)>2);
 assertPlantedLegs(contact);
});

test('continuous guard keeps fixed limbs, planted feet and natural projected wrist angles for early/late blocks',()=>{
 for(const hitAt of [null,0,30,140,350,479,550,579])for(let ms=0;ms<=580;ms++){
  const impactAge=hitAt===null||ms<hitAt?null:ms-hitAt,p=sharedGuardPose(ms,impactAge,guard,rig);
  assertPlantedLegs(p);
  for(const a of Object.values(p.arms)){
   assert.ok(Math.abs(distance(a.shoulder,a.elbow)-a.upper)<1e-6);
   assert.ok(Math.abs(distance(a.elbow,a.wrist)-a.fore)<1e-6);
   assert.ok(Math.abs(a.wristDeflection)<35);
  }
  assert.ok(p.weapon.registrationError<1e-6);
 }
});
test('guard starts and ends at ready, and blocking never jumps to another pose',()=>{
 const ready=thrustPose(0,guard,rig);
 for(const ms of [0,140,480,580]){
  const a=sharedGuardPose(ms-1e-5,null,guard,rig),b=sharedGuardPose(ms+1e-5,null,guard,rig);
  for(const name of Object.keys(a.transforms)){
   assert.ok(distance(a.transforms[name].point,b.transforms[name].point)<1e-5);
   assert.ok(Math.abs(a.transforms[name].angle-b.transforms[name].angle)<1e-5);
  }
 }
 for(const ms of [0,580]){
  const p=sharedGuardPose(ms,null,guard,rig);assert.deepEqual(p.transforms,ready.transforms);assert.deepEqual(p.weapon.tip,ready.weapon.tip);
 }
 for(const ms of [0,30,140,350,479,550,579]){
  const before=sharedGuardPose(ms,null,guard,rig),after=sharedGuardPose(ms,0,guard,rig);
  assert.deepEqual(before.transforms,after.transforms);assert.deepEqual(before.weapon.tip,after.weapon.tip);
 }
});
test('guard recoil clock freezes with pause/hitstop and clears on reset/new guard',()=>{
 const s=new CombatState(track,()=>{},read('shared-sweep-track'));s.startDuel();s.duel.stage='windup';s.duel.age=500;s.defend();s.update(250);s.update(100);
 assert.equal(s.duel.blockAge,0);s.update(30);assert.equal(s.duel.blockAge,30);const held=sharedHeroPose(s,guard,rig);
 s.paused=true;s.update(200);assert.deepEqual(sharedHeroPose(s,guard,rig),held);s.paused=false;s.freeze=70;s.update(40);assert.deepEqual(sharedHeroPose(s,guard,rig),held);
 s.reset();assert.equal(s.duel.blockAge,null);s.duel.blockAge=30;s.defend();assert.equal(s.duel.blockAge,null);
});
