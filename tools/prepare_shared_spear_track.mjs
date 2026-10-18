import fs from 'node:fs';
import {thrustPose,sweepPose} from '../docs/routes/jigoku-2d/combat/hero-rig.mjs';
const out='docs/routes/jigoku-2d/combat',read=n=>JSON.parse(fs.readFileSync(`${out}/${n}.json`));
const guard=read('guard-rig'),rig=read('thrust-rig');
const poses=Array.from({length:36},(_,i)=>thrustPose(i,guard,rig));
fs.writeFileSync(`${out}/shared-spear-track.json`,JSON.stringify({fps:30,activeFrames:[14,15],frames:poses.map(p=>p.weapon.tip),note:'Blade endpoint from the same rigid-spear transform rendered in Phaser. 36 simulated frames; original active window and duration retained. Legacy spear-track.json remains for archived sweep boundary art.'},null,2)+'\n');
console.log(JSON.stringify({first:poses[0].weapon.tip,contact:poses[14].weapon.tip,maxWristDeflection:Object.fromEntries(['rear','front'].map(s=>[s,Math.max(...poses.map(p=>Math.abs(p.arms[s].wristDeflection)))]))}));

const sweep=Array.from({length:32},(_,i)=>sweepPose(i,guard,rig));
const phases=Array.from({length:32},(_,i)=>i<4?0:i<9?1:i<14?2:i<19?3:i<24?4:5);
fs.writeFileSync(`${out}/shared-sweep-track.json`,JSON.stringify({fps:30,activeFrames:Array.from({length:8},(_,i)=>i+9),frames:sweep.map(p=>p.weapon.tip),poseFrames:phases,phaseLabels:['prepare','descend','contact','follow','rise','ready'],note:'32-frame fixed-camera low arc from shared waist/arm rig and the same spear. Phases are timing labels, not separate body textures. Active frames 9..16 and original duration retained.'},null,2)+'\n');
console.log(JSON.stringify({sweepContact:sweep[9].weapon.tip,sweepMaxWristDeflection:Object.fromEntries(['rear','front'].map(s=>[s,Math.max(...sweep.map(p=>Math.abs(p.arms[s].wristDeflection)))]))}));
