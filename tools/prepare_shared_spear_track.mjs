import fs from 'node:fs';
import {thrustPose} from '../docs/routes/jigoku-2d/combat/hero-rig.mjs';
const out='docs/routes/jigoku-2d/combat',read=n=>JSON.parse(fs.readFileSync(`${out}/${n}.json`));
const guard=read('guard-rig'),rig=read('thrust-rig');
const poses=Array.from({length:36},(_,i)=>thrustPose(i,guard,rig));
fs.writeFileSync(`${out}/shared-spear-track.json`,JSON.stringify({fps:30,activeFrames:[14,15],frames:poses.map(p=>p.weapon.tip),note:'Blade endpoint from the same rigid-spear transform rendered in Phaser. 36 simulated frames; original active window and duration retained. Legacy spear-track.json remains for archived sweep boundary art.'},null,2)+'\n');
console.log(JSON.stringify({first:poses[0].weapon.tip,contact:poses[14].weapon.tip,maxWristDeflection:Object.fromEntries(['rear','front'].map(s=>[s,Math.max(...poses.map(p=>Math.abs(p.arms[s].wristDeflection)))]))}));
