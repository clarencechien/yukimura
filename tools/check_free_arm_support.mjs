import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {supportPose} from '../docs/routes/jigoku-2d/free-arm-support/rig.mjs';
const meta=JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/free-arm-support/support.json')),distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6);
test('support reach keeps fixed arm lengths, reachable targets and bounded projected wrist angle',()=>{
 for(let age=330;age<=540;age+=.25){const p=supportPose(age,meta);near(distance(p.shoulder,p.elbow),85);near(distance(p.elbow,p.wrist),90);near(distance(p.wrist,p.target),0);assert.ok(p.distance<=170);assert.ok(Math.abs(p.wristDeflection)<=25);assert.equal(p.handAngle,0);}
});
test('plant fixes the painted palm-heel landmark while chest sinks and elbow flexes',()=>{
 const first=supportPose(420,meta),last=supportPose(500,meta);near(last.chestY-first.chestY,8);assert.ok(distance(first.elbow,last.elbow)>5);
 for(let age=420;age<=540;age+=.5){const p=supportPose(age,meta);assert.ok(p.planted);near(distance(p.heel,p.contact),0);near(distance(p.wrist,first.wrist),0);near(p.handAngle,first.handAngle);}
 assert.equal(supportPose(419.999,meta).planted,false);
});
test('reach and load boundaries are continuous, finite and deterministic for pause/seek',()=>{
 for(const age of [330,420,500,540]){const a=supportPose(age-1e-4,meta),b=supportPose(age+1e-4,meta);for(const n of ['shoulder','elbow','wrist','heel'])assert.ok(distance(a[n],b[n])<.001);}
 assert.deepEqual(supportPose(465,meta),supportPose(465,meta));assert.deepEqual(supportPose(-1,meta),supportPose(330,meta));assert.throws(()=>supportPose(NaN,meta));
});
