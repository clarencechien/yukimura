import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {fallPose} from '../docs/routes/jigoku-2d/free-arm-settle/fall.mjs';
import {sharedShoulderPose} from '../docs/routes/jigoku-2d/free-arm-settle/shared-shoulder.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL('../docs/routes/jigoku-2d/'+p,import.meta.url))),m=read('free-arm-settle/shared-shoulder.json'),settle=read('free-arm-settle/settle.json'),transition=read('free-arm-transition/transition.json'),kit=read('free-arm-parts/parts.json'),support=read('free-arm-support/support.json'),fall=read('free-arm-settle/bridge.json');
const body=t=>fallPose(t,settle,transition,kit,support,fall),pose=t=>sharedShoulderPose(t,body(t),m);
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);
test('activation reassembles the existing bridge cap without an attachment jump',()=>{
 const p=body(m.start),q=pose(m.start),f=fall.frames[p.fallFrame];assert.equal(f.id,'bridge');assert.equal(q.angle,0);
 near(q.point.x-m.cap.pivot[0],p.fallOffset.x);near(q.point.y-m.cap.pivot[1],p.fallOffset.y);
});
test('collar mount and cap angle remain continuous across body cuts; arm socket is unchanged',()=>{
 for(let t=m.start;t<=m.end;t+=.5){const p=body(t),before=JSON.stringify(p),q=sharedShoulderPose(t,p,m);assert.equal(JSON.stringify(p),before);near(q.point.x-p.shoulder.x,q.offset.x);near(q.point.y-p.shoulder.y,q.offset.y);assert.ok(q.offset.y>=-20&&q.offset.y<=0);assert.ok(q.angle>=0&&q.angle<=14);}
 for(const t of [1220,1240,1260,1320,1380,1440,1500]){const a=pose(t-.001),b=pose(t+.001);assert.ok(Math.hypot(a.point.x-b.point.x,a.point.y-b.point.y)<.002);assert.ok(Math.abs(a.angle-b.angle)<.002);}
});
test('seeking is deterministic, endpoint holds and invalid time is rejected',()=>{
 const first=pose(1320);pose(1800);pose(1180);assert.deepEqual(pose(1320),first);assert.deepEqual(pose(1500),pose(1800));assert.throws(()=>sharedShoulderPose(NaN,body(1220),m),/finite/);
});
