import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {guardRigPose} from '../docs/routes/jigoku-2d/combat/guard-rig.mjs';
import {DuelState} from '../docs/routes/jigoku-2d/combat/duel-state.mjs';
const rig=JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/combat/guard-rig.json'));
test('all guard poses retain one spear length and fixed grip anchors; palm registration stays under 3 px',()=>{
 const widths=[];for(let i=0;i<4;i++){const p=guardRigPose(i,rig);widths.push(p.width);assert.ok(Math.abs(Math.hypot(p.tip.x-p.butt.x,p.tip.y-p.butt.y)-760)<1e-6);assert.ok(Math.abs(Math.hypot(p.front.x-p.rear.x,p.front.y-p.rear.y)-237)<1e-6);assert.ok(p.registrationError<3);const a=p.palms[1],b=p.rear,c=p.tip;assert.ok(Math.abs((a.x-b.x)*(c.y-b.y)-(a.y-b.y)*(c.x-b.x))<1e-6);assert.ok(p.angle<0);for(const q of [p.butt,p.tip])assert.ok(q.x>=0&&q.x<=1200&&q.y>=0&&q.y<=750);}
 assert.ok(widths.every(w=>w===widths[0]));assert.equal(guardRigPose(null,rig),null);
});
test('guard includes lift and lower without changing defensive duration or recovery cooldown',()=>{
 const s=new DuelState(()=>{});s.enabled=true;s.defend();const poses=new Set();for(let i=0;i<580;i++){poses.add(s.guardPose);s.update(1,'near');}assert.deepEqual([...poses],[0,1,3]);assert.equal(s.guardPose,null);assert.equal(s.cooldown,520);assert.equal(s.defend(),false);
});
test('blocked guard shows absorb between lift and lower; reset clears the layered pose',()=>{
 const s=new DuelState(()=>{});s.enabled=true;s.stage='windup';s.age=500;s.defend();const poses=new Set();for(let i=0;i<580;i++){poses.add(s.guardPose);s.update(1,'near');}assert.deepEqual([...poses],[0,1,2,3]);assert.equal(s.playerHP,3);assert.equal(s.blocks,1);s.reset();assert.equal(s.guardPose,null);
});
