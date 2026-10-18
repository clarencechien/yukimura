import fs from 'node:fs';import test from 'node:test';import assert from 'node:assert/strict';
import {fittedArm} from '../docs/routes/jigoku-2d/free-arm-parts/rig.mjs';
const meta=JSON.parse(fs.readFileSync('docs/routes/jigoku-2d/free-arm-parts/parts.json'));
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),near=(a,b)=>assert.ok(Math.abs(a-b)<1e-6);
function endpoint(t,m,end){const angle=t.angle*Math.PI/180,x=end[0]-m.pivot[0],y=end[1]-m.pivot[1];return{x:t.point.x+x*Math.cos(angle)-y*Math.sin(angle),y:t.point.y+x*Math.sin(angle)+y*Math.cos(angle)};}
test('textured arm anchors match fixed bones throughout the fitted reach',()=>{
 for(let age=180;age<=420;age+=.5){const p=fittedArm(age,meta);near(dist(p.shoulder,p.elbow),85);near(dist(p.elbow,p.wrist),90);assert.deepEqual(p.shoulder,{x:516,y:394.2});near(dist(p.parts[1].point,p.elbow),0);near(dist(endpoint(p.parts[0],meta.parts.upper,meta.parts.upper.end),p.elbow),0);near(dist(endpoint(p.parts[1],meta.parts.fore,meta.parts.fore.end),p.wrist),0);near(dist(p.parts[2].point,p.wrist),0);near(p.handAngle,p.foreAngle);}
});
test('two hand states share the wrist socket and manual selection does not alter the bones',()=>{
 assert.equal(fittedArm(259,meta).hand,'relax');assert.equal(fittedArm(260,meta).hand,'open');
 for(const age of [180,250,330,420]){const a=fittedArm(age,meta,'relax'),b=fittedArm(age,meta,'open');for(const k of ['shoulder','elbow','wrist'])assert.deepEqual(a[k],b[k]);near(a.handAngle,b.handAngle);}
 assert.throws(()=>fittedArm(250,meta,'unknown'));
});
