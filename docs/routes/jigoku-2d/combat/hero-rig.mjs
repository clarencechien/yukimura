import {guardRigPose,rigidSpearPose} from './guard-rig.mjs';
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
// Fixed segment lengths and a fixed elbow branch; targets outside the reach envelope
// are errors, never silently stretched or clamped away from the spear.
function arm(j,shoulder,wrist){
 const upper=length(sub(j.elbow,j.shoulder)),fore=length(sub(j.wrist,j.elbow));
 const v=sub(wrist,shoulder),d=length(v);
 if(d>upper+fore+1e-6||d<Math.abs(upper-fore)-1e-6)throw Error('Unreachable hero wrist');
 const along=(upper*upper-fore*fore+d*d)/(2*d),off=Math.sqrt(Math.max(0,upper*upper-along*along))*j.bend;
 const elbow=[shoulder[0]+v[0]/d*along-v[1]/d*off,shoulder[1]+v[1]/d*along+v[0]/d*off];
 return {shoulder,elbow,wrist,upper,fore,upperAngle:deg(angle(sub(elbow,shoulder))-angle(sub(j.elbow,j.shoulder))),foreAngle:deg(angle(sub(wrist,elbow))-angle(sub(j.wrist,j.elbow)))};
}
export function thrustPose(frame,guardRig,rig){
 const drive=envelope(frame),rest=guardRig.poses[3].grips,restAngle=angle(sub(rest[1],rest[0]));
 const axis=drive>=0?restAngle+(rad(-7)-restAngle)*drive:restAngle+rad(1)*drive;
 const shift=drive>=0?[26*drive,-4*drive]:[24*drive,-4*drive];
 const rear=add(rest[0],shift),front=add(rear,[Math.cos(axis)*237,Math.sin(axis)*237]);
 const turn=rad(drive>=0?10*drive:3*drive),handTurn=axis-restAngle;
 const transforms={lower:{point:[0,0],angle:0},torso:{point:rig.hip,angle:deg(turn)}};const arms={};
 for(const [side,grip] of [['rear',rear],['front',front]]){
  const j=rig.joints[side],shoulder=add(rig.hip,rot(sub(j.shoulder,rig.hip),turn));
  const wrist=add(grip,rot(sub(j.wrist,j.grip),handTurn));const solved=arm(j,shoulder,wrist);arms[side]=solved;
  solved.grip=grip;solved.handAngle=deg(handTurn);
  solved.wristDeflection=deg(angle(sub(grip,wrist))-angle(sub(wrist,solved.elbow)));
  transforms[side+'Upper']={point:shoulder,angle:solved.upperAngle};transforms[side+'Fore']={point:solved.elbow,angle:solved.foreAngle};transforms[side+'Hand']={point:wrist,angle:deg(handTurn)};
 }
 return {action:'thrust',frame,transforms,arms,weapon:rigidSpearPose({grips:[rear,front]},guardRig.weapon,frame)};
}
export function sharedHeroPose(state,guardRig,rig){
 if(state.duel.guardPose!==null){const frame=state.duel.guardPose;return {action:'guard',frame,weapon:guardRigPose(frame,guardRig)};}
 if(state.phase==='attack'&&state.attackKind==='sweep')return null;
 const p=thrustPose(state.phase==='attack'?state.frame:0,guardRig,rig);p.action=state.phase==='attack'?'thrust':'idle';return p;
}
