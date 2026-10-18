import {enemyArm,closedGrip} from './enemy-arm.mjs';
// Blade size stays constant. The release transform is independent of later body poses.
export function enemyWeapon(enemy,age,dead,rig){
  const held=!dead||age<rig.releaseAge;
  const arm=enemyArm(held?enemy:{pose:6,alpha:enemy.alpha},held?age:rig.releaseAge,dead,rig);
  const {grip,angle}=closedGrip(arm,rig);
  if(held)return {held:true,landed:false,wrist:arm.wrist,grip,angle,alpha:enemy.alpha};
  const t=Math.max(0,Math.min(1,(age-rig.releaseAge)/rig.flightMs));
  const ground=rig.groundY-(rig.parts.katana.size[1]-rig.parts.katana.pivot[1]);
  return {held:false,landed:t===1,wrist:arm.wrist,grip:{x:grip.x+40*t,y:grip.y-40*t+(ground-grip.y+40)*t*t},angle:angle*(1-t),alpha:enemy.alpha};
}
export function enemyPointToWorld(point,targetX,rig){return {x:targetX+(point.x-rig.bodyOrigin[0])*rig.worldScale,y:574+(point.y-rig.bodyOrigin[1])*rig.worldScale};}
