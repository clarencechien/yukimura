const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
// Authored rigid slide; alpha-cell hull keeps the boot at its final projected height.
export function sharedRearLegPose(age,meta){
 if(!Number.isFinite(age))throw Error('finite age required');
 let a=meta.keys[0],b=a;
 for(let i=1;i<meta.keys.length;i++){b=meta.keys[i];if(age<=b.time)break;a=b;}
 const t=a.time===b.time?0:ease((age-a.time)/(b.time-a.time));
 const angle=a.angle+(b.angle-a.angle)*t,x=a.x+(b.x-a.x)*t,r=angle*Math.PI/180;
 const support=Math.max(...meta.leg.hull.map(([x,y])=>x*Math.sin(r)+y*Math.cos(r)));
 return {point:{x:meta.leg.pivot[0]+x,y:meta.contactY-support},angle};
}
