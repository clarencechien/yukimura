const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
// A collar mount relative to the unchanged arm socket; deterministic on seek.
export function sharedShoulderPose(age,pose,meta){
 if(!Number.isFinite(age))throw Error('finite age required');
 const keys=[{time:meta.start,angle:0,offset:[0,0]},...meta.keys];
 let a=keys[0],b=a;
 for(let i=1;i<keys.length;i++){b=keys[i];if(age<=b.time)break;a=b;}
 const t=a.time===b.time?0:ease((age-a.time)/(b.time-a.time));
 const offset={x:a.offset[0]+(b.offset[0]-a.offset[0])*t,y:a.offset[1]+(b.offset[1]-a.offset[1])*t};
 return {point:{x:pose.shoulder.x+offset.x,y:pose.shoulder.y+offset.y},offset,angle:a.angle+(b.angle-a.angle)*t};
}
