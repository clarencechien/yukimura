import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {settlePose,rotate} from '../docs/routes/jigoku-2d/free-arm-settle/rig.mjs';
import {yieldPose,yieldSword,YIELD} from '../docs/routes/jigoku-2d/free-arm-settle/yield.mjs';
import {releasingSword} from '../docs/routes/jigoku-2d/free-arm-settle/release.mjs';
const read=p=>JSON.parse(fs.readFileSync(`docs/routes/jigoku-2d/${p}`)),m=read('free-arm-settle/settle.json'),tr=read('free-arm-transition/transition.json'),k=read('free-arm-parts/parts.json'),s=read('free-arm-support/support.json'),rig=read('combat/enemy-rig.json'),rel=read('free-arm-settle/release.json');
const base=t=>settlePose(t,m,tr,k,s),pose=t=>yieldPose(t,m,tr,k,s),weapon=t=>yieldSword(t,pose(t),m,rig,releasingSword(t,base(t),m,rig,rel)),d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6,`${a} vs ${b}`);
test('previous settling remains exact until unloading; lower body and folded legs do not move',()=>{
 for(let t=330;t<=860;t+=.25)assert.deepEqual(pose(t),base(t));
 for(let t=860;t<=1500;t+=.25)assert.deepEqual(pose(t).leg,base(860).leg);
 assert.deepEqual(pose(1180),pose(1500));assert.throws(()=>pose(NaN));
});
test('unloading torso maps shoulder exactly, arms remain fixed-length without IK clamping and supported wrist stays bounded',()=>{
 for(let t=860.1;t<=1500;t+=.25){const p=pose(t),h=p.torso,v=rotate({x:m.shoulder[0]-h.pivot.x,y:m.shoulder[1]-h.pivot.y},h.angle);near(p.shoulder.x,h.pivot.x+h.offset.x+v.x);near(p.shoulder.y,h.pivot.y+h.offset.y+v.y);
  near(d(p.shoulder,p.elbow),85);near(d(p.elbow,p.wrist),90);near(d(p.wrist,p.target),0);
  const a=weapon(t);near(d(a.shoulder,a.elbow),65);near(d(a.elbow,a.wrist),75);near(d(a.wrist,a.target),0);
  if(p.planted){assert.deepEqual(p.heel,{x:470,y:668});assert.ok(Math.abs(p.wristDeflection)<=25);}
 }
});
test('palm pivots about its heel until lift, wrist stays continuous through hand swap, blade remains world-fixed',()=>{
 for(let t=860.1;t<1000;t+=.1){const p=pose(t),q=rotate({x:s.palm.heel[0]-s.palm.pivot[0],y:s.palm.heel[1]-s.palm.pivot[1]},p.handAngle);near(p.wrist.x+q.x,470);near(p.wrist.y+q.y,668);}
 for(const t of [860,1000,1180]){const a=pose(t-.001),b=pose(t+.001);assert.ok(d(a.shoulder,b.shoulder)<.01);assert.ok(d(a.wrist,b.wrist)<.01);assert.ok(d(weapon(t-.001).wrist,weapon(t+.001).wrist)<.01);}
 const grounded=weapon(860);for(let t=860;t<=1500;t+=.25){const a=weapon(t);for(const key of ['grip','bladeAngle','bounds','grounded','phase'])assert.deepEqual(a[key],grounded[key]);}
 assert.equal(pose(1000).planted,false);assert.equal(pose(1000).parts[2].name,'open');assert.equal(pose(1000).heel,null);
 const p=pose(1090),a=weapon(1090);for(const t of [1500,330,1000,860]){pose(t);weapon(t);}assert.deepEqual(pose(1090),p);assert.deepEqual(weapon(1090),a);
});
