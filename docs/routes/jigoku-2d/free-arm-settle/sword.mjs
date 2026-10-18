import {solveArm,closedGrip} from '../combat/enemy-arm.mjs';
import {rotate} from './rig.mjs';

// Hand-authored projected socket inside the far side of the chest, not a
// measured anatomical landmark. The late socket uses the SAME torso matrix.
export const SWORD_SOCKET_OFFSET={x:-95,y:-28};
export function settlingSword(p,meta,rig){
 let shoulder;
 if(p.late){
  const h=p.torso,v=rotate({x:meta.shoulder[0]+SWORD_SOCKET_OFFSET.x-h.pivot.x,y:meta.shoulder[1]+SWORD_SOCKET_OFFSET.y-h.pivot.y},h.angle);
  shoulder={x:h.pivot.x+h.offset.x+v.x,y:h.pivot.y+h.offset.y+v.y};
 }else shoulder={x:p.shoulder.x+SWORD_SOCKET_OFFSET.x,y:p.shoulder.y+SWORD_SOCKET_OFFSET.y};
 const t=Math.max(0,Math.min(1,(p.age-330)/170)),u=t*t*(3-2*t);
 const target={x:shoulder.x-75+5*u,y:shoulder.y+70+5*u};
 const arm=solveArm(shoulder,target,...rig.armLengths),held=closedGrip(arm,rig);
 return {...arm,target,grip:held.grip,handAngle:held.angle,bladeAngle:held.angle,held:true};
}
