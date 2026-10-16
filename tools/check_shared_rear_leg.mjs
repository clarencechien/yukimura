import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {sharedRearLegPose} from '../docs/routes/jigoku-2d/free-arm-settle/shared-rear-leg.mjs';
const meta=JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/free-arm-settle/shared-rear-leg.json'));
test('reusable boot slides monotonically with stable projected contact and rigid scale',()=>{
 let last=-Infinity;
 for(let t=1200;t<=1800;t+=.5){const p=sharedRearLegPose(t,meta),r=p.angle*Math.PI/180;assert.ok(p.point.x>=last);last=p.point.x;
  const bottom=Math.max(...meta.leg.hull.map(([x,y])=>p.point.y+x*Math.sin(r)+y*Math.cos(r)));
  assert.ok(Math.abs(bottom-meta.contactY)<1e-9);assert.ok(bottom<meta.groundY);assert.equal(p.angle,0);
 }
});
test('no position jump across body drawing changes; seeks and endpoints are deterministic',()=>{
 for(const t of [1200,1240,1260,1320,1380,1440,1500]){const a=sharedRearLegPose(t-.001,meta),b=sharedRearLegPose(t+.001,meta);assert.ok(Math.hypot(a.point.x-b.point.x,a.point.y-b.point.y)<.002);}
 assert.deepEqual(sharedRearLegPose(1500,meta),sharedRearLegPose(1800,meta));
 assert.deepEqual(sharedRearLegPose(1500,meta).point,{x:meta.leg.pivot[0],y:meta.leg.pivot[1]});
 const a=sharedRearLegPose(1320,meta);sharedRearLegPose(1800,meta);assert.deepEqual(sharedRearLegPose(1320,meta),a);assert.throws(()=>sharedRearLegPose(NaN,meta));
});
