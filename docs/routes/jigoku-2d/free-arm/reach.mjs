// Diagnostic projected 2D reach only. This module does not drive the combat sprites.
import {solveArm} from '../combat/enemy-arm.mjs';
export const LENGTHS=[85,90];
export const RESERVE=5;
export const MARKS={
 buckle:{frame:3,shoulder:[600,341],elbow:[640,407],wrist:[563,430]},
 crouch:{frame:4,shoulder:[507,384],elbow:[510,470],wrist:[476,537]},
 kneel:{frame:5,shoulder:[523,448],elbow:[517,558],wrist:[473,650]},
 candidate:{frame:5,shoulder:[520.5,476.25],elbow:[519,573.75],wrist:[477.75,656.25]},
};
const point=([x,y])=>({x,y});
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
export function assess(mark){
 const shoulder=point(mark.shoulder),target=point(mark.wrist);
 const pose=solveArm(shoulder,target,...LENGTHS),distance=dist(shoulder,target);
 return {distance,reachable:distance<175&&distance>5,overreach:Math.max(0,distance-175),miss:dist(pose.wrist,target),paintedLengths:[dist(shoulder,point(mark.elbow)),dist(point(mark.elbow),target)],pose};
}
// Planning target: lower shoulder vertically, keep wrist target fixed, reserve
// 5 px from full extension. No texture, torso or source landmark is transformed.
export function shoulderPlan(mark){
 const [sx,sy]=mark.shoulder,[wx,wy]=mark.wrist,max=LENGTHS[0]+LENGTHS[1]-RESERVE;
 if(Math.abs(wx-sx)>=max||wy<=sy)throw Error('Vertical shoulder lowering cannot solve this pose');
 const y=Math.max(sy,wy-Math.sqrt(max*max-(wx-sx)**2));
 return {...mark,shoulder:[sx,y],lowering:y-sy};
}
export function trajectory(age,{planned=false,candidate=false}={}){
 if(!Number.isFinite(age))throw Error('Non-finite diagnostic time');
 const t=Math.max(180,Math.min(420,age));
 const keys=[[180,MARKS.buckle],[250,MARKS.crouch],[330,candidate?MARKS.candidate:MARKS.kneel],[420,candidate?MARKS.candidate:MARKS.kneel]];
 let a=keys[0],b=keys[1];
 for(let i=1;i<keys.length;i++){a=keys[i-1];b=keys[i];if(t<=b[0])break;}
 const u=(t-a[0])/(b[0]-a[0]),f=u*u*(3-2*u);
 const from=planned?shoulderPlan(a[1]):a[1],to=planned?shoulderPlan(b[1]):b[1];
 const lerp=(p,q)=>p.map((v,i)=>v+(q[i]-v)*f);
 const shoulder=point(lerp(from.shoulder,to.shoulder)),target=point(lerp(from.wrist,to.wrist));
 const pose=solveArm(shoulder,target,...LENGTHS),distance=dist(shoulder,target);
 return {...pose,target,age:t,distance,reachable:distance<175&&distance>5,miss:dist(pose.wrist,target),frame:t<250?3:t<330?4:5,planned};
}
