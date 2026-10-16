import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {sharedHeadPose} from '../docs/routes/jigoku-2d/free-arm-settle/shared-head.mjs';import {yieldPose} from '../docs/routes/jigoku-2d/free-arm-settle/yield.mjs';import {rotate} from '../docs/routes/jigoku-2d/free-arm-settle/rig.mjs';
const read=p=>JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/'+p)),meta=read('free-arm-settle/shared-head.json'),body=yieldPose(1180,read('free-arm-settle/settle.json'),read('free-arm-transition/transition.json'),read('free-arm-parts/parts.json'),read('free-arm-support/support.json')),pose=t=>sharedHeadPose(t,body,meta),distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
test('shared head starts in the exact existing torso transform, including painted pivot',()=>{
 const h=pose(1180);assert.equal(h.angle,body.torso.angle);
 for(const [x,y] of [meta.head.box.slice(0,2),meta.head.box.slice(2),meta.head.pivot]){
  const a=rotate({x:x-meta.head.pivot[0],y:y-meta.head.pivot[1]},h.angle),b=rotate({x:x-body.torso.pivot.x,y:y-body.torso.pivot.y},body.torso.angle);
  assert.ok(distance({x:a.x+h.point.x,y:a.y+h.point.y},{x:b.x+body.torso.pivot.x+body.torso.offset.x,y:b.y+body.torso.pivot.y+body.torso.offset.y})<1e-9);
 }
});
test('head trajectory is continuous across every body-image handoff and stays rigid',()=>{
 for(const t of [1180,1200,1220,1240,1260,1320,1380,1440,1500]){assert.ok(distance(pose(t-.001).point,pose(t+.001).point)<.01);assert.ok(Math.abs(pose(t-.001).angle-pose(t+.001).angle)<.01);}
 const width=meta.head.box[2]-meta.head.box[0];for(let t=1180;t<=1500;t+=.2){const v=rotate({x:width,y:0},pose(t).angle);assert.ok(Math.abs(Math.hypot(v.x,v.y)-width)<1e-9);}
});
test('authored head keys, final hold and backward scrubbing remain deterministic',()=>{
 for(const k of meta.keys)assert.deepEqual(pose(k.time),{point:{x:k.point[0],y:k.point[1]},angle:k.angle});
 const before=pose(1235);for(const t of [1800,1180,1450])pose(t);assert.deepEqual(pose(1235),before);assert.deepEqual(pose(1800),pose(1500));assert.throws(()=>pose(NaN));
});
