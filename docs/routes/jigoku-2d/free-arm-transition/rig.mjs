import {solveArm} from '../combat/enemy-arm.mjs';
import {supportPose} from '../free-arm-support/rig.mjs';
import {fittedArm} from '../free-arm-parts/rig.mjs';
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
const lerp=(a,b,t)=>a+(b-a)*t;
export function transitionPose(age,meta,kit,support){
 if(!Number.isFinite(age))throw Error('Invalid transition time');
 const t=Math.max(330,Math.min(540,age));
 let p,index;
 if(t>=420){p=supportPose(t,support);index=4;}
 else{
  const keys=meta.frames;let i=0;while(i<keys.length-2&&t>keys[i+1].time)i++;
  const a=keys[i],b=keys[i+1],u=ease((t-a.time)/(b.time-a.time));
  const shoulder={x:lerp(a.shoulder[0],b.shoulder[0],u),y:lerp(a.shoulder[1],b.shoulder[1],u)};
  const start=fittedArm(330,kit),end=supportPose(420,support),s=ease((t-330)/90);
  const target={x:shoulder.x+lerp(start.wrist.x-start.shoulder.x,end.wrist.x-end.shoulder.x,s),y:shoulder.y+lerp(start.wrist.y-start.shoulder.y,end.wrist.y-end.shoulder.y,s)};
  const distance=Math.hypot(target.x-shoulder.x,target.y-shoulder.y);if(distance>170.000001||distance<5)throw Error('Unreachable arm target');
  const arm=solveArm(shoulder,target,85,90),handAngle=(arm.foreAngle+90-support.palm.axisDegrees)*(1-s),r=handAngle*Math.PI/180;
  const hx=support.palm.heel[0]-support.palm.pivot[0],hy=support.palm.heel[1]-support.palm.pivot[1];
  p={...arm,age:t,target,distance,handAngle,wristDeflection:handAngle+support.palm.axisDegrees-(arm.foreAngle+90),heel:{x:arm.wrist.x+hx*Math.cos(r)-hy*Math.sin(r),y:arm.wrist.y+hx*Math.sin(r)+hy*Math.cos(r)},contact:end.contact,planted:false,load:0,shadowAlpha:.08+.32*s,shadowWidth:65-20*s};
  p.parts=[{name:'upper',point:shoulder,angle:arm.upperAngle},{name:'fore',point:arm.elbow,angle:arm.foreAngle},{name:'palm',point:arm.wrist,angle:handAngle}];
  index=keys.reduce((best,f,n)=>Math.abs(f.time-t)<Math.abs(keys[best].time-t)?n:best,0);
 }
 const frame=meta.frames[index],bodyOffset={x:p.shoulder.x-frame.shoulder[0],y:p.shoulder.y-frame.shoulder[1]};
 return {...p,index,frame:frame.id,bodyOffset};
}
export function endpointPose(age,meta,kit,support){return transitionPose(age<375?330:Math.max(420,age),meta,kit,support);}
