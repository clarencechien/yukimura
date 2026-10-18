import {yieldPose,yieldSword} from './yield.mjs';
import {solveArm} from '../combat/enemy-arm.mjs';
import {rotate} from './rig.mjs';
import {SWORD_SOCKET_OFFSET} from './sword.mjs';
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);},mix=(a,b,t)=>({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t});
export function fallPose(age,settle,transition,kit,support,meta){
 const p=yieldPose(age,settle,transition,kit,support);
 if(age<=meta.start)return p;
 const keys=[{time:meta.start,shoulder:[p.shoulder.x,p.shoulder.y]},...meta.frames];
 let a=keys[0],b=keys.at(-1);for(let i=1;i<keys.length;i++){b=keys[i];if(age<=b.time)break;a=b;}
 const t=a.time===b.time?0:ease((age-a.time)/(b.time-a.time)),shoulder=mix({x:a.shoulder[0],y:a.shoulder[1]},{x:b.shoulder[0],y:b.shoulder[1]},t);
 const u=ease((age-meta.start)/(meta.end-meta.start)),target=mix(p.wrist,{x:meta.nearWrist[0],y:meta.nearWrist[1]},u),arm=solveArm(shoulder,target,85,90);
 let key=0;for(let i=1;i<keys.length;i++)if(Math.abs(age-keys[i].time)<Math.abs(age-keys[key].time))key=i;
 const fallFrame=key-1,bodyOffset=fallFrame>=0?{x:shoulder.x-meta.frames[fallFrame].shoulder[0],y:shoulder.y-meta.frames[fallFrame].shoulder[1]}:null;
 const torso={...p.torso,offset:{x:p.torso.offset.x+shoulder.x-p.shoulder.x,y:p.torso.offset.y+shoulder.y-p.shoulder.y}};
 const handAngle=arm.foreAngle+90-kit.parts.open.axisDegrees;
 return {...p,...arm,target,torso,fallFrame,fallProgress:u,fallOffset:bodyOffset,handAngle,distance:Math.hypot(target.x-shoulder.x,target.y-shoulder.y),parts:[{name:'upper',point:shoulder,angle:arm.upperAngle},{name:'fore',point:arm.elbow,angle:arm.foreAngle},{name:'open',point:arm.wrist,angle:handAngle}]};
}
export function fallSword(age,p,settle,rig,weapon,baseBody,meta){
 const base=yieldSword(age,baseBody,settle,rig,weapon);
 if(age<=meta.start)return base;
 const u=ease((age-meta.start)/(meta.end-meta.start)),offset=rotate(SWORD_SOCKET_OFFSET,baseBody.torso.angle),shoulder={x:p.shoulder.x+offset.x,y:p.shoulder.y+offset.y};
 const target=mix(base.wrist,{x:meta.farWrist[0],y:meta.farWrist[1]},u),arm=solveArm(shoulder,target,...rig.armLengths);
 return {...base,...arm,target,handAngle:arm.foreAngle+90-rig.parts.open.axisDegrees};
}
