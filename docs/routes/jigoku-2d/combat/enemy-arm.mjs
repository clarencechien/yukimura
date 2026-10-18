import {enemyBinding} from './duel-poses.mjs';
import {DUEL_TIMING} from './duel-state.mjs';
import {enemyBodyPose,recoilValue,lowRecoilValue,fatalBlend} from './enemy-body.mjs';
const degrees=180/Math.PI;
export function solveArm(shoulder,target,upperLength,foreLength){
  const dx=target.x-shoulder.x,dy=target.y-shoulder.y,raw=Math.hypot(dx,dy);
  const ux=raw>1e-8?dx/raw:0,uy=raw>1e-8?dy/raw:1;
  const d=Math.max(Math.abs(upperLength-foreLength)+1e-4,Math.min(upperLength+foreLength-1e-4,raw));
  const along=(upperLength**2-foreLength**2+d*d)/(2*d),height=Math.sqrt(Math.max(0,upperLength**2-along**2));
  // Fixed bend side keeps the tucked elbow from flipping across the arm axis.
  const elbow={x:shoulder.x+ux*along+uy*height,y:shoulder.y+uy*along-ux*height};
  const wrist={x:shoulder.x+ux*d,y:shoulder.y+uy*d};
  return {shoulder,elbow,wrist,upperAngle:Math.atan2(elbow.y-shoulder.y,elbow.x-shoulder.x)*degrees-90,foreAngle:Math.atan2(wrist.y-elbow.y,wrist.x-elbow.x)*degrees-90};
}
function localTarget(age,dead,rig,low=false){
  const keys=low?(dead?[[0,12],[110,13],[250,3],[330,4],[420,5],[500,6],[540,10],[580,11],[640,7],[720,8],[1000,9]]:[[0,12],[110,13],[260,14],[340,15],[420,0]]):dead?[[0,0],[90,1],[180,2],[250,3],[330,4],[420,5],[500,6],[540,10],[580,11],[640,7],[720,8],[1000,9]]:[[0,0],[90,1],[160,2],[260,1],[360,0]];
  let a=keys[0],b=keys.at(-1);
  for(let i=1;i<keys.length;i++){if(age<keys[i][0]){a=keys[i-1];b=keys[i];break;}a=keys[i];}
  const t=b[0]===a[0]?0:Math.max(0,Math.min(1,(age-a[0])/(b[0]-a[0]))),blend=t*t*(3-2*t);
  const offset=index=>{const v=rig.bindings[index];return [v.wrist[0]-v.shoulder[0],v.wrist[1]-v.shoulder[1]];};
  const from=offset(a[1]),to=offset(b[1]);return {x:from[0]+(to[0]-from[0])*blend,y:from[1]+(to[1]-from[1])*blend};
}
export function enemyArm(enemy,age,dead,rig){
  const body=enemyBodyPose(enemy,rig),binding=enemyBinding(body?0:enemy.pose,rig),shoulder=body?.shoulder??{x:binding.shoulder[0],y:binding.shoulder[1]},offset=localTarget(age,dead,rig,enemy.reaction==='sweep');
  if(enemy.intent){
    // Shoulder follows the same rigid torso transform used by the renderer.
    const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
    let from=[3,110],to=[3,110],t=0;
    if(enemy.intent==='windup'){to=[-39,98];t=ease(enemy.intentAge/DUEL_TIMING.windup);}
    if(enemy.intent==='strike'){from=[-39,98];to=[35,110];t=ease(enemy.intentAge/DUEL_TIMING.strike);}
    if(enemy.intent==='recovery'&&enemy.recoveryFrom==='attack'){from=[35,110];t=ease(enemy.intentAge/520);}
    offset.x=from[0]+(to[0]-from[0])*t;offset.y=from[1]+(to[1]-from[1])*t;
  }
  if(enemy.bodyReaction){
    const {from,fromAge,age:hitAge}=enemy.bodyReaction,start=enemyArm(from,fromAge,false,rig);
    const x=start.wrist.x-start.shoulder.x,y=start.wrist.y-start.shoulder.y;
    const low=enemy.bodyReaction.kind==='sweep',curve=low?lowRecoilValue:recoilValue;
    if(enemy.bodyReaction.fatal){
     // Match the exact legacy reach at the buckle boundary, including sweep's
     // distinct reach curve, so hand and held sword remain attached.
     const target=localTarget(180,true,rig,low),t=fatalBlend(hitAge);
     offset.x=x+(target.x-x)*t;offset.y=y+(target.y-y)*t;
    }else{
     offset.x=curve(x,x+(low?-6:6),3,hitAge);offset.y=curve(y,y+(low?4:-5),110,hitAge);
    }
  }
  const arm=solveArm(shoulder,{x:shoulder.x+offset.x,y:shoulder.y+offset.y},rig.armLengths[0],rig.armLengths[1]);
  const handState=dead?(age>=rig.releaseAge?'open':age>=rig.relaxAge?'relax':'grip'):'grip';
  const hand=rig.parts[handState],handAngle=arm.foreAngle+90-hand.axisDegrees;
  return {...arm,handState,handAngle,alpha:enemy.alpha};
}
export function closedGrip(arm,rig){
  const hand=rig.parts.grip,angle=(arm.foreAngle+90-hand.axisDegrees),a=angle/ degrees;
  const dx=hand.gripPoint[0]-hand.pivot[0],dy=hand.gripPoint[1]-hand.pivot[1];
  return {grip:{x:arm.wrist.x+dx*Math.cos(a)-dy*Math.sin(a),y:arm.wrist.y+dx*Math.sin(a)+dy*Math.cos(a)},angle};
}
