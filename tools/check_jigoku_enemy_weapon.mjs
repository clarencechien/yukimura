import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {enemyWeapon,enemyPointToWorld} from '../docs/routes/jigoku-2d/combat/enemy-weapon.mjs';
import {enemyArm,solveArm} from '../docs/routes/jigoku-2d/combat/enemy-arm.mjs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
const base=new URL('../docs/routes/jigoku-2d/combat/',import.meta.url);
const rig=JSON.parse(fs.readFileSync(new URL('enemy-rig.json',base)));
const track=JSON.parse(fs.readFileSync(new URL('spear-track.json',base)));
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} != ${b}`);
test('all held poses keep the same wrist-to-grip distance and valid sockets',()=>{
 const hand=rig.parts.grip,length=Math.hypot(hand.gripPoint[0]-hand.pivot[0],hand.gripPoint[1]-hand.pivot[1]);
 assert.equal(rig.bindings.length,10);
 for(let pose=0;pose<7;pose++){
  const w=enemyWeapon({pose,alpha:1},0,false,rig);assert.equal(w.held,true);
  near(Math.hypot(w.grip.x-w.wrist.x,w.grip.y-w.wrist.y),length);
  const p=enemyPointToWorld(w.wrist,970,rig),q=enemyPointToWorld(w.wrist,1060,rig);near(q.x-p.x,90);near(q.y,p.y);
 }
});
test('release begins at the last held grip and lands on a fixed plane without stretching',()=>{
 const held=enemyWeapon({pose:6,alpha:1},499.999999,true,rig);
 const release=enemyWeapon({pose:7,alpha:1},500,true,rig);
 near(held.grip.x,release.grip.x);near(held.grip.y,release.grip.y);near(held.angle,release.angle);assert.equal(release.held,false);
 const land=enemyWeapon({pose:9,alpha:.5},780,true,rig);assert.equal(land.landed,true);near(land.angle,0);
 near(land.grip.y+rig.parts.katana.size[1]-rig.parts.katana.pivot[1],rig.groundY);
 const later=enemyWeapon({pose:9,alpha:0},1700,true,rig);assert.deepEqual(later.grip,land.grip);assert.equal(later.alpha,0);
});
test('pause freezes drop; reset restores held weapon',()=>{
 const s=new CombatState(track);s.hp=0;s.enemyHit=true;s.enemyAge=600;s.paused=true;
 const get=()=>enemyWeapon(s.enemy,s.enemyAge,s.hp===0,rig),before=get();s.update(200);assert.deepEqual(get(),before);
 s.paused=false;s.update(200);assert.equal(get().landed,true);s.reset();assert.equal(get().held,true);assert.equal(get().alpha,1);
});

test('two-bone solve preserves both lengths for all poses and unreachable/zero targets',()=>{
 for(let pose=0;pose<10;pose++)for(let age=0;age<=1700;age+=17){
  const arm=enemyArm({pose,alpha:1},age,true,rig);
  near(Math.hypot(arm.elbow.x-arm.shoulder.x,arm.elbow.y-arm.shoulder.y),65);
  near(Math.hypot(arm.wrist.x-arm.elbow.x,arm.wrist.y-arm.elbow.y),75);
 }
 for(const target of [{x:0,y:0},{x:10000,y:0},{x:-10000,y:-10000}]){
  const arm=solveArm({x:0,y:0},target,65,75);near(Math.hypot(arm.elbow.x,arm.elbow.y),65);near(Math.hypot(arm.wrist.x-arm.elbow.x,arm.wrist.y-arm.elbow.y),75);
 }
});
test('local reach is continuous across curve keys and hands relax before blade release',()=>{
 for(const age of [90,160,180,250,260,330,360,420,500,580,720,1000]){
  const a=enemyArm({pose:6,alpha:1},age-1e-5,true,rig),b=enemyArm({pose:6,alpha:1},age+1e-5,true,rig);
  assert.ok(Math.hypot(a.wrist.x-b.wrist.x,a.wrist.y-b.wrist.y)<.001);
 }
 assert.equal(enemyArm({pose:6,alpha:1},429,true,rig).handState,'grip');
 assert.equal(enemyArm({pose:6,alpha:1},430,true,rig).handState,'relax');
 assert.equal(enemyWeapon({pose:6,alpha:1},430,true,rig).held,true);
 assert.equal(enemyArm({pose:7,alpha:1},500,true,rig).handState,'open');
 assert.equal(enemyArm({pose:6,alpha:1},600,false,rig).handState,'grip');
});
