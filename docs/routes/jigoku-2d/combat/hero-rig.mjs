import {rigidSpearPose} from './guard-rig.mjs';
import {DUEL_TIMING} from './duel-state.mjs';
const rad=d=>d*Math.PI/180,deg=a=>a*180/Math.PI;
const add=(a,b)=>[a[0]+b[0],a[1]+b[1]],sub=(a,b)=>[a[0]-b[0],a[1]-b[1]];
const rot=(v,a)=>[v[0]*Math.cos(a)-v[1]*Math.sin(a),v[0]*Math.sin(a)+v[1]*Math.cos(a)];
const angle=v=>Math.atan2(v[1],v[0]);
const length=v=>Math.hypot(...v);
const smooth=t=>t*t*(3-2*t);
function envelope(frame){
 const keys=[[0,0],[5,-1],[9,-1],[14,1],[16,1],[24,0],[35,0]];
 for(let i=1;i<keys.length;i++)if(frame<=keys[i][0]){const [a,x]=keys[i-1],[b,y]=keys[i];return x+(y-x)*smooth((frame-a)/(b-a));}
 return 0;
}
// Fixed segment lengths and a fixed elbow/knee branch; targets outside the reach envelope
// are errors, never silently stretched or clamped away from the spear.
function arm(j,shoulder,wrist){
 const upper=length(sub(j.elbow,j.shoulder)),fore=length(sub(j.wrist,j.elbow));
 const v=sub(wrist,shoulder),d=length(v);
 if(d>upper+fore+1e-6||d<Math.abs(upper-fore)-1e-6)throw Error('Unreachable hero limb target');
 const along=(upper*upper-fore*fore+d*d)/(2*d),off=Math.sqrt(Math.max(0,upper*upper-along*along))*j.bend;
 const elbow=[shoulder[0]+v[0]/d*along-v[1]/d*off,shoulder[1]+v[1]/d*along+v[0]/d*off];
 return {shoulder,elbow,wrist,upper,fore,upperAngle:deg(angle(sub(elbow,shoulder))-angle(sub(j.elbow,j.shoulder))),foreAngle:deg(angle(sub(wrist,elbow))-angle(sub(j.wrist,j.elbow)))};
}
export function thrustPose(frame,guardRig,rig){
 const drive=envelope(frame),rest=guardRig.poses[3].grips,restAngle=angle(sub(rest[1],rest[0]));
 const axis=drive>=0?restAngle+(rad(-7)-restAngle)*drive:restAngle+rad(1)*drive;
 const shift=drive>=0?[26*drive,-4*drive]:[24*drive,-4*drive];
 const rear=add(rest[0],shift);
 return articulatedPose(rear,axis,rad(drive>=0?10*drive:3*drive),frame,guardRig,rig,'thrust',drive>=0?[5*drive,4*drive]:[3*drive,-3*drive]);
}
export function articulatedPose(rear,axis,turn,frame,guardRig,rig,action,root=[0,0]){
 const rest=guardRig.poses[3].grips,restAngle=angle(sub(rest[1],rest[0]));
 const front=add(rear,[Math.cos(axis)*guardRig.weapon.gripDistance,Math.sin(axis)*guardRig.weapon.gripDistance]),handTurn=axis-restAngle;
 const pelvis=add(rig.hip,root);
 const transforms={lower:{point:pelvis,angle:0},torso:{point:pelvis,angle:deg(turn)}};const arms={},legs={};
 for(const [side,j] of Object.entries(rig.legs)){
  const solved=arm({shoulder:j.hip,elbow:j.knee,wrist:j.ankle,bend:j.bend},add(j.hip,root),j.ankle);
  legs[side]={hip:solved.shoulder,knee:solved.elbow,ankle:solved.wrist,thigh:solved.upper,shin:solved.fore};
  transforms[side+'Thigh']={point:solved.shoulder,angle:solved.upperAngle};
  transforms[side+'Shin']={point:solved.elbow,angle:solved.foreAngle};
  transforms[side+'Foot']={point:j.ankle,angle:0};
 }
 for(const [side,grip] of [['rear',rear],['front',front]]){
  const j=rig.joints[side],shoulder=add(pelvis,rot(sub(j.shoulder,rig.hip),turn));
  const wrist=add(grip,rot(sub(j.wrist,j.grip),handTurn));const solved=arm(j,shoulder,wrist);arms[side]=solved;
  solved.grip=grip;solved.handAngle=deg(handTurn);
  solved.wristDeflection=deg(angle(sub(grip,wrist))-angle(sub(wrist,solved.elbow)));
  transforms[side+'Upper']={point:shoulder,angle:solved.upperAngle};transforms[side+'Fore']={point:solved.elbow,angle:solved.foreAngle};transforms[side+'Hand']={point:wrist,angle:deg(handTurn)};
 }
 return {action,frame,transforms,arms,legs,root,weapon:rigidSpearPose({grips:[rear,front]},guardRig.weapon,frame)};
}
// Low arc in the fixed camera plane. Waist leads the blade, with identical
// endpoints to ready/thrust. No pose swap or independent spear interpolation.
export function sweepPose(frame,guardRig,rig){
 const rest=guardRig.poses[3].grips,restAngle=angle(sub(rest[1],rest[0]));
 const keys=[
  [0,...rest[0],restAngle,0,0,0],
  [3,351,314,rad(-15),-2,-3,4],
  [9,340,275,rad(17),12,2,8],
  [16,350,278,rad(20),16,5,6],
  [24,...rest[0],restAngle,0,0,0],
  [31,...rest[0],restAngle,0,0,0]
 ];
 let values=keys.at(-1).slice(1);
 for(let i=1;i<keys.length;i++)if(frame<=keys[i][0]){
  const a=keys[i-1],b=keys[i],t=smooth((frame-a[0])/(b[0]-a[0]));
  values=a.slice(1).map((v,j)=>v+(b[j+1]-v)*t);break;
 }
 const [x,y,axis,turn,dx,dy]=values;
 return articulatedPose([x,y],axis,rad(turn),frame,guardRig,rig,'sweep',[dx,dy]);
}
// Continuous raised guard using the same shoulders, fixed limbs and planted feet.
// Recoil starts at zero on impact, so a block cannot jump to a different silhouette.
export function sharedGuardPose(elapsed,impactAge,guardRig,rig){
 const t=Math.max(0,Math.min(DUEL_TIMING.guard,elapsed));
 const lift=smooth(Math.min(1,t/140)),lower=smooth(Math.max(0,(t-(DUEL_TIMING.guard-100))/100));
 const weight=lift*(1-lower);
 const recoil=impactAge===null?0:impactAge<55?smooth(Math.max(0,impactAge)/55):1-smooth(Math.min(1,(impactAge-55)/105));
 const absorb=recoil*weight,rest=guardRig.poses[3].grips;
 const axis=angle(sub(rest[1],rest[0]));
 const p=articulatedPose([rest[0][0]-9*weight-2*absorb,rest[0][1]-43*weight+3*absorb],axis+(rad(-20)-axis)*weight,rad(3*weight),t,guardRig,rig,'guard',[-3*weight-absorb,4*weight+2*absorb]);
 p.guard={elapsed:t,weight,recoil:absorb,impactAge};return p;
}
export function sharedHeroPose(state,guardRig,rig){
 if(state.duel.guardPose!==null)return sharedGuardPose(DUEL_TIMING.guard-state.duel.guard,state.duel.blockAge,guardRig,rig);
 if(state.phase==='attack'&&state.attackKind==='sweep')return sweepPose(state.frame,guardRig,rig);
 const p=thrustPose(state.phase==='attack'?state.frame:0,guardRig,rig);p.action=state.phase==='attack'?'thrust':'idle';return p;
}
