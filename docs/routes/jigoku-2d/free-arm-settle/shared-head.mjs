import {rotate} from './rig.mjs';
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
export function sharedHeadPose(age,unload,meta){
 if(!Number.isFinite(age))throw Error('finite age required');
 const pivot=meta.head.pivot,torso=unload.torso,v=rotate({x:pivot[0]-torso.pivot.x,y:pivot[1]-torso.pivot.y},torso.angle);
 const first={time:meta.start,point:[torso.pivot.x+torso.offset.x+v.x,torso.pivot.y+torso.offset.y+v.y],angle:torso.angle};
 if(age<=meta.start)return {point:{x:first.point[0],y:first.point[1]},angle:first.angle};
 const keys=[first,...meta.keys];let a=keys[0],b=keys.at(-1);for(let i=1;i<keys.length;i++){b=keys[i];if(age<=b.time)break;a=b;}
 const t=a.time===b.time?0:ease((age-a.time)/(b.time-a.time));return {point:{x:a.point[0]+(b.point[0]-a.point[0])*t,y:a.point[1]+(b.point[1]-a.point[1])*t},angle:a.angle+(b.angle-a.angle)*t};
}
