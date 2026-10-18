import {solveArm} from '../combat/enemy-arm.mjs';
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
export const CONTACT_MS=420;
export function supportPose(age,meta){
 if(!Number.isFinite(age))throw Error('Invalid support time');
 const t=Math.max(330,Math.min(540,age)),reach=ease((t-330)/90),load=ease((t-420)/80);
 const chestY=-10*(1-reach)+8*load;
 const shoulder={x:meta.body.shoulder[0],y:meta.body.shoulder[1]+chestY};
 const heelOffset={x:meta.palm.heel[0]-meta.palm.pivot[0],y:meta.palm.heel[1]-meta.palm.pivot[1]};
 const end={x:meta.contact[0]-heelOffset.x,y:meta.contact[1]-heelOffset.y};
 const start={x:490,y:630},target={x:start.x+(end.x-start.x)*reach,y:start.y+(end.y-start.y)*reach};
 const distance=Math.hypot(target.x-shoulder.x,target.y-shoulder.y);if(distance>170||distance<5)throw Error('Support target exceeds reserved fixed-arm reach');
 const arm=solveArm(shoulder,target,85,90),heel={x:arm.wrist.x+heelOffset.x,y:arm.wrist.y+heelOffset.y};
 const handAngle=0,wristDeflection=handAngle+meta.palm.axisDegrees-(arm.foreAngle+90);
 return {...arm,age:t,chestY,target,heel,contact:{x:meta.contact[0],y:meta.contact[1]},planted:t>=420,handAngle,wristDeflection,distance,load,shadowAlpha:.12+.28*reach,shadowWidth:55-10*reach,parts:[{name:'upper',point:shoulder,angle:arm.upperAngle},{name:'fore',point:arm.elbow,angle:arm.foreAngle},{name:'palm',point:arm.wrist,angle:handAngle}]};
}
