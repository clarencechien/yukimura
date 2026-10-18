import {settlingSword} from './sword.mjs';
import {rotate} from './rig.mjs';
import {solveArm} from '../combat/enemy-arm.mjs';
const clamp=t=>Math.max(0,Math.min(1,t)),ease=t=>{t=clamp(t);return t*t*(3-2*t);};
export function bladeBounds(point,angle,rig,meta){
 const pivot=rig.parts.katana.pivot;
 const vertices=meta.bladeHull.map(([x,y])=>{const q=rotate({x:x-pivot[0],y:y-pivot[1]},angle);return {x:q.x+point.x,y:q.y+point.y};});
 return {left:Math.min(...vertices.map(p=>p.x)),right:Math.max(...vertices.map(p=>p.x)),bottom:Math.max(...vertices.map(p=>p.y))};
}
// Body holds its existing 540 ms end pose while the hand and blade finish.
// No cached release state: arbitrary scrubbing uses the same release transform.
export function releasingSword(age,body,settle,rig,meta){
 if(!Number.isFinite(age))throw new TypeError('age must be finite');
 const held=settlingSword(body,settle,rig);
 if(age<meta.releaseAge)return {...held,handState:'grip',phase:'held',grounded:false,bounds:bladeBounds(held.grip,held.bladeAngle,rig,meta)};
 const t=clamp((age-meta.releaseAge)/(meta.landAge-meta.releaseAge)),u=ease(t),reach=ease((age-meta.releaseAge)/meta.handReturnMs);
 const target={x:held.target.x+meta.handReturn[0]*reach,y:held.target.y+meta.handReturn[1]*reach};
 const arm=solveArm(held.shoulder,target,...rig.armLengths),handState=age<meta.openAge?'relax':'open';
 const bladeAngle=held.bladeAngle*(1-u),bottom=bladeBounds({x:0,y:0},bladeAngle,rig,meta).bottom;
 const freeY=held.grip.y+meta.fallDistance*t*t,ceiling=meta.groundY-bottom;
 const grip={x:held.grip.x+meta.driftX*u,y:Math.min(freeY,ceiling)},grounded=freeY>=ceiling;
 return {...arm,target,grip,handAngle:arm.foreAngle+90-rig.parts[handState].axisDegrees,bladeAngle,held:false,handState,grounded,phase:t===1?'settled':grounded?'contact':'falling',releaseGrip:held.grip,bounds:bladeBounds(grip,bladeAngle,rig,meta)};
}
