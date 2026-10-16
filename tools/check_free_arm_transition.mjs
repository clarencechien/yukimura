import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {transitionPose} from '../docs/routes/jigoku-2d/free-arm-transition/rig.mjs';import {supportPose} from '../docs/routes/jigoku-2d/free-arm-support/rig.mjs';import {fittedArm} from '../docs/routes/jigoku-2d/free-arm-parts/rig.mjs';
const read=p=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/${p}`)),m=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),pose=t=>transitionPose(t,m,k,s),d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} vs ${b}`);
test('full transition keeps fixed arm lengths and wrist bounds without stretching',()=>{
 for(let t=330;t<=540;t+=.1){const p=pose(t);near(d(p.shoulder,p.elbow),85);near(d(p.elbow,p.wrist),90);near(d(p.wrist,p.target),0);assert.ok(Math.abs(p.wristDeflection)<=25);if(t<420)assert.ok(p.heel.y<=p.contact.y+1e-6);}
});
test('initial arm matches fitted crouch and support segment is unchanged at every time',()=>{
 const first=fittedArm(330,k);for(const n of ['shoulder','elbow','wrist'])near(d(pose(330)[n],first[n]),0);
 for(let t=420;t<=540;t+=.5){const p=pose(t),old=supportPose(t,s);for(const n of ['shoulder','elbow','wrist','heel'])near(d(p[n],old[n]),0);near(d(p.heel,p.contact),0);assert.equal(p.index,4);}
});
test('shoulder and arm remain continuous through all image changes and motion keys',()=>{
 for(const t of [330,341,352,364,376,388,400,410,420,500,540]){const a=pose(t-1e-5),b=pose(t+1e-5);for(const n of ['shoulder','elbow','wrist','heel'])assert.ok(d(a[n],b[n])<.001);}
 for(let t=330;t<=540;t+=.5){const p=pose(t),f=m.frames[p.index];near(f.shoulder[0]+p.bodyOffset.x,p.shoulder.x);near(f.shoulder[1]+p.bodyOffset.y,p.shoulder.y);}
});
test('four pre-kneel front soles register within one pixel; five drawn poses are visited',()=>{
 const first=m.frames[0].registration.frontSole;for(const f of m.frames.slice(0,4)){const foot=f.registration.frontSole;assert.ok(Math.hypot(foot[0]-first[0],foot[1]-first[1])<1);}
 assert.deepEqual(m.frames.map(f=>pose(f.time).index),[0,1,2,3,4]);
});
test('seek is deterministic, clamps endpoints and rejects invalid time',()=>{assert.deepEqual(pose(390),pose(390));assert.deepEqual(pose(0),pose(330));assert.deepEqual(pose(999),pose(540));assert.throws(()=>pose(NaN));});
