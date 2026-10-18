import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {fallPose} from '../docs/routes/jigoku-2d/free-arm-settle/fall.mjs';
import {shoulderEntryPose} from '../docs/routes/jigoku-2d/free-arm-settle/shoulder-entry.mjs';
import {rotate} from '../docs/routes/jigoku-2d/free-arm-settle/rig.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../docs/routes/jigoku-2d/'+p,import.meta.url))),m=read('free-arm-settle/shoulder-entry.json'),settle=read('free-arm-settle/settle.json'),transition=read('free-arm-transition/transition.json'),kit=read('free-arm-parts/parts.json'),support=read('free-arm-support/support.json'),fall=read('free-arm-settle/bridge.json');
const body=t=>fallPose(t,settle,transition,kit,support,fall),pose=t=>shoulderEntryPose(t,body(t),m),near=(a,b)=>assert.ok(Math.hypot(a.x-b.x,a.y-b.y)<1e-8,JSON.stringify({a,b}));
test('independent cap begins in the original chest transform at palm release',()=>{
 const p=body(m.start),q=pose(m.start);assert.equal(p.planted,false);assert.equal(q.progress,0);assert.equal(q.angle,p.torso.angle);
 for(const x of [m.cap.box[0],m.cap.box[2]])for(const y of [m.cap.box[1],m.cap.box[3]]){
  const a=rotate({x:x-p.torso.pivot.x,y:y-p.torso.pivot.y},p.torso.angle),b=rotate({x:x-m.cap.pivot[0],y:y-m.cap.pivot[1]},q.angle);
  near({x:a.x+p.torso.pivot.x+p.torso.offset.x,y:a.y+p.torso.pivot.y+p.torso.offset.y},{x:b.x+q.point.x,y:b.y+q.point.y});
 }
});
test('drop follows the unchanged skeleton continuously and reaches the registered side-fall plate',()=>{
 let progress=-1;
 for(let t=m.start;t<=m.end;t+=.2){const p=body(t),saved=JSON.stringify(p),q=shoulderEntryPose(t,p,m);assert.equal(JSON.stringify(p),saved);assert.ok(q.progress>=progress);progress=q.progress;near(q.point,{x:p.shoulder.x+q.offset.x,y:p.shoulder.y+q.offset.y});}
 for(const t of [1000,1100,1180,1200]){const a=pose(t-.001),b=pose(t+.001);assert.ok(Math.hypot(a.point.x-b.point.x,a.point.y-b.point.y)<.003);assert.ok(Math.abs(a.angle-b.angle)<.003);}
 const end=pose(m.end);assert.equal(end.angle,m.target.angle);assert.deepEqual(end.offset,{x:m.target.offset[0],y:m.target.offset[1]});assert.equal(body(m.end).torso.angle,m.collar.referenceTorsoAngle);
});
test('reverse seeking is deterministic; cap pose rejects invalid input',()=>{
 const q=pose(1100);pose(1200);pose(1000);assert.deepEqual(pose(1100),q);assert.throws(()=>shoulderEntryPose(NaN,body(1000),m),/finite/);
});
