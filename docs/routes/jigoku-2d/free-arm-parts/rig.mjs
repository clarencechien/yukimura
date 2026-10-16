import {trajectory} from '../free-arm/reach.mjs';
// Fitting pass: reuse the planned relative arm path on ONE stationary crouch.
// No claim that its hand reaches the floor or that the torso follows the old rig.
export function fittedArm(age,meta,handMode='auto'){
 const p=trajectory(age,{planned:true}),anchor={x:meta.body.shoulder[0],y:meta.body.shoulder[1]};
 const move=q=>({x:anchor.x+q.x-p.shoulder.x,y:anchor.y+q.y-p.shoulder.y});
 const hand=handMode==='auto'?(p.age<260?'relax':'open'):handMode;
 if(!['relax','open'].includes(hand))throw Error('Unknown hand state');
 return {...p,shoulder:anchor,elbow:move(p.elbow),wrist:move(p.wrist),target:move(p.target),hand,handAngle:p.foreAngle,parts:[
  {name:'upper',point:anchor,angle:p.upperAngle},
  {name:'fore',point:move(p.elbow),angle:p.foreAngle},
  {name:hand,point:move(p.wrist),angle:p.foreAngle},
 ]};
}
