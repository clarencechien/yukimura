import {settlePose,rotate} from './rig.mjs';
import {solveArm} from '../combat/enemy-arm.mjs';
import {settlingSword} from './sword.mjs';
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
export const YIELD={start:860,release:1000,end:1180,reviewEnd:1500,torsoRotation:-18,torsoShift:{x:-16,y:3},palmRoll:10,freeWrist:{x:445,y:650},farReachLift:30};
export function yieldPose(age,meta,transition,kit,support){
 const p=settlePose(age,meta,transition,kit,support);
 if(age<=YIELD.start)return p;
 const u=ease((age-YIELD.start)/(YIELD.end-YIELD.start));
 const torso={...p.torso,angle:p.torso.angle+YIELD.torsoRotation*u,offset:{x:p.torso.offset.x+YIELD.torsoShift.x*u,y:p.torso.offset.y+YIELD.torsoShift.y*u}};
 const q=rotate({x:meta.shoulder[0]-torso.pivot.x,y:meta.shoulder[1]-torso.pivot.y},torso.angle);
 const shoulder={x:torso.pivot.x+torso.offset.x+q.x,y:torso.pivot.y+torso.offset.y+q.y};
 const roll=YIELD.palmRoll*ease((age-YIELD.start)/(YIELD.release-YIELD.start)),heelOffset={x:support.palm.heel[0]-support.palm.pivot[0],y:support.palm.heel[1]-support.palm.pivot[1]};
 const offset=rotate(heelOffset,roll),start={x:p.contact.x-offset.x,y:p.contact.y-offset.y};
 const leave=ease((age-YIELD.release)/(YIELD.end-YIELD.release));
 const target={x:start.x+(YIELD.freeWrist.x-start.x)*leave,y:start.y+(YIELD.freeWrist.y-start.y)*leave};
 const arm=solveArm(shoulder,target,85,90),planted=age<YIELD.release,hand=planted?'palm':'open',handAngle=planted?roll:arm.foreAngle+90-kit.parts.open.axisDegrees;
 const heel=planted?{...p.contact}:null;
 return {...p,...arm,torso,target,planted,heel,handAngle,distance:Math.hypot(target.x-shoulder.x,target.y-shoulder.y),wristDeflection:planted?handAngle+support.palm.axisDegrees-(arm.foreAngle+90):0,unload:u,handState:hand,shadowAlpha:p.shadowAlpha*(1-leave),parts:[{name:'upper',point:shoulder,angle:arm.upperAngle},{name:'fore',point:arm.elbow,angle:arm.foreAngle},{name:hand,point:arm.wrist,angle:handAngle}]};
}
// The released blade's transform stays in world space. Only its former arm
// follows the moving torso; never feed the yielded body back into release.mjs.
export function yieldSword(age,p,settle,rig,weapon){
 if(age<=YIELD.start)return weapon;
 const u=ease((age-YIELD.start)/(YIELD.end-YIELD.start)),socket=settlingSword(p,settle,rig).shoulder;
 const target={x:socket.x+weapon.target.x-weapon.shoulder.x,y:socket.y+weapon.target.y-weapon.shoulder.y-YIELD.farReachLift*u};
 const arm=solveArm(socket,target,...rig.armLengths);
 return {...weapon,...arm,target,handAngle:arm.foreAngle+90-rig.parts.open.axisDegrees};
}
