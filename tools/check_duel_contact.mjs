import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {CombatState} from '../docs/routes/jigoku-2d/combat/combat-state.mjs';
import {sharedHeroPose} from '../docs/routes/jigoku-2d/combat/hero-rig.mjs';
import {duelContactPose} from '../docs/routes/jigoku-2d/combat/duel-contact.mjs';
import {enemyArm,closedGrip} from '../docs/routes/jigoku-2d/combat/enemy-arm.mjs';
const read=n=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/combat/${n}.json`)),g=read('guard-rig'),h=read('thrust-rig'),r=read('enemy-rig');r.duelBindings=read('duel-art').enemy.bindings;
const create=emit=>{const s=new CombatState(read('shared-spear-track'),emit,read('shared-sweep-track'));s.startDuel();return s;};
const pose=s=>duelContactPose(s,sharedHeroPose(s,g,h),g,h,r);
const advance=(s,ms)=>{for(let i=0;i<ms;i++)s.update(1);};
const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(distance(a,b)<1e-6);
function fixed(p){assert.ok(Math.abs(distance(p.arm.shoulder,p.arm.elbow)-65)<1e-6);assert.ok(Math.abs(distance(p.arm.elbow,p.arm.wrist)-75)<1e-6);near(p.weapon.grip,closedGrip(p.arm,r).grip);assert.equal(p.weapon.angle,p.arm.handAngle);}
test('early and late blocks meet the actual painted blade with fixed arm lengths and grip',()=>{
 for(const press of [1471,1500,1700,1750,1900,2000,2049]){
  const s=create();let contacts=0;
  for(let t=0;t<2450;t++){
   if(t===press)s.defend();const p=pose(s);fixed(p);
   if(p.contact?.weight===1){
    const m=p.contact.mark,a=p.weapon.angle*Math.PI/180,dx=m.x-r.parts.katana.pivot[0],dy=m.y-r.parts.katana.pivot[1];
    const actual={x:970+(p.weapon.grip.x+dx*Math.cos(a)-dy*Math.sin(a)-576)*.6,y:574+(p.weapon.grip.y+dx*Math.sin(a)+dy*Math.cos(a)-690)*.6};
    near(actual,p.contact.target);assert.ok(m.x>=14&&m.x<=170);contacts++;
    if(s.duel.guarding)near(actual,sharedHeroPose(s,g,h).weapon.contact);
   }
   s.update(1);
  }
  assert.ok(contacts);assert.equal(s.duel.blocks,1);assert.equal(s.duel.playerHP,3);
 }
});
test('pressing guard late begins from the existing arm without an input-frame snap',()=>{
 for(const t of [1700,1900,2049]){const s=create();advance(s,t);const before=pose(s);s.defend();assert.deepEqual(pose(s).arm,before.arm);assert.equal(pose(s).contact,null);}
});
test('the block event itself has coincident blade and shaft coordinates',()=>{
 let eventPose=null;const s=create(e=>{if(e.type==='block')eventPose=pose(s);});advance(s,1750);s.defend();advance(s,300);
 assert.ok(eventPose);assert.equal(eventPose.contact.weight,1);near(eventPose.contact.point,eventPose.contact.target);assert.equal(s.duel.guardAtBlock,280);
});
test('contact releases after the hold and returns to ordinary motion by 300 ms',()=>{
 const s=create();advance(s,1750);s.defend();advance(s,300);
 advance(s,65);assert.equal(pose(s).contact.weight,1);advance(s,1);assert.ok(pose(s).contact.weight<1);advance(s,234);assert.equal(pose(s).contact,null);
 assert.deepEqual(pose(s).arm,enemyArm(s.enemy,s.enemyAge,false,r));
 const lateEnd=create(),rest=sharedHeroPose(lateEnd,g,h).weapon.contact;advance(lateEnd,1500);lateEnd.defend();advance(lateEnd,581);assert.ok(lateEnd.attack());advance(lateEnd,100);
 near(pose(lateEnd).contact.target,rest);assert.ok(distance(sharedHeroPose(lateEnd,g,h).weapon.contact,rest)>1,'Counterattack moves independently from the previous clash');
});
test('far misses and expired guards never acquire a blocked contact',()=>{
 const far=create();far.setRange('far');advance(far,1750);far.defend();advance(far,300);assert.equal(pose(far).contact,null);assert.equal(far.duel.blocks,0);
 const early=create();advance(early,1200);early.defend();advance(early,850);assert.equal(pose(early).contact,null);assert.equal(early.duel.playerHP,2);
});
test('pause and hitstop freeze the constrained arm; reset and interruption clear contact',()=>{
 const s=create();advance(s,1750);s.defend();advance(s,330);const p=pose(s);s.paused=true;s.update(200);assert.deepEqual(pose(s),p);
 s.paused=false;s.freeze=70;s.update(50);assert.deepEqual(pose(s),p);s.reset();assert.equal(pose(s).contact,null);assert.equal(s.duel.guardAtBlock,null);
 advance(s,1750);s.defend();advance(s,300);s.enemyHit=true;s.enemyAge=0;s.duel.interrupt();assert.equal(pose(s).contact,null);
});
