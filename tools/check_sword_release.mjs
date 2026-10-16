import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {settlePose} from '../docs/routes/jigoku-2d/free-arm-settle/rig.mjs';
import {settlingSword} from '../docs/routes/jigoku-2d/free-arm-settle/sword.mjs';
import {releasingSword} from '../docs/routes/jigoku-2d/free-arm-settle/release.mjs';
const read=p=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/${p}`)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),rig=read('combat/enemy-rig.json'),release=read('free-arm-settle/release.json');
const body=t=>settlePose(t,m,tr,k,s),pose=t=>releasingSword(t,body(t),m,rig,release),d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} vs ${b}`);
test('held motion is unchanged; blade and wrist cross release without a position or rotation jump',()=>{
 for(let t=330;t<540;t+=.25){const a=pose(t),b=settlingSword(body(t),m,rig);for(const key of Object.keys(b))assert.deepEqual(a[key],b[key]);}
 const a=pose(539.999),b=pose(540.001);near(d(a.grip,b.grip),0);near(d(a.wrist,b.wrist),0);near(a.bladeAngle,b.bladeAngle);assert.equal(a.handState,'grip');assert.equal(b.handState,'relax');
});
test('released arm stays reachable, hand separates, palm remains planted and blade never crosses projected ground',()=>{
 for(let t=540;t<=1000;t+=.25){const p=pose(t);near(d(p.shoulder,p.elbow),65);near(d(p.elbow,p.wrist),75);near(d(p.wrist,p.target),0);assert.ok(p.bounds.bottom<=release.groundY+1e-6);if(p.grounded)near(p.bounds.bottom,release.groundY);assert.deepEqual(body(t).heel,{x:470,y:668});}
 assert.ok(d(pose(860).grip,pose(860).wrist)>50);assert.equal(pose(600).handState,'open');assert.equal(pose(860).phase,'settled');
});
test('release and landing can be scrubbed backwards, resting blade is stable and invalid times rejected',()=>{
 const a=pose(860);for(const t of [1000,330,700,540,860])pose(t);assert.deepEqual(a,pose(860));assert.deepEqual(pose(860),pose(1000));assert.throws(()=>pose(NaN));
 for(const t of [540,600,760,860]){const a=pose(t-.001),b=pose(t+.001);assert.ok(d(a.grip,b.grip)<.01);assert.ok(d(a.wrist,b.wrist)<.01);assert.ok(Math.abs(a.bladeAngle-b.bladeAngle)<.01);}
});
