// Rigid image components: never resize the blade or glove between poses.
export function enemyWeapon(enemy, age, dead, rig){
  const binding=rig.bindings[Math.min(enemy.pose,6)];
  const wrist={x:binding.wrist[0],y:binding.wrist[1]};
  const hand=rig.parts.grip,theta=binding.angle*Math.PI/180;
  const dx=hand.gripPoint[0]-hand.pivot[0],dy=hand.gripPoint[1]-hand.pivot[1];
  const grip={x:wrist.x+dx*Math.cos(theta)-dy*Math.sin(theta),y:wrist.y+dx*Math.sin(theta)+dy*Math.cos(theta)};
  const held=!dead||age<rig.releaseAge;
  if(held)return {held:true,landed:false,wrist,grip,angle:binding.angle,alpha:enemy.alpha};
  // Release from the last held socket, independent of the later body's pose switches.
  const t=Math.max(0,Math.min(1,(age-rig.releaseAge)/rig.flightMs));
  const ground=rig.groundY-(rig.parts.katana.size[1]-rig.parts.katana.pivot[1]);
  return {held:false,landed:t===1,wrist,grip:{x:grip.x+40*t,y:grip.y-40*t+(ground-grip.y+40)*t*t},angle:binding.angle*(1-t),alpha:enemy.alpha};
}
export function enemyPointToWorld(point,targetX,rig){return {x:targetX+(point.x-rig.bodyOrigin[0])*rig.worldScale,y:574+(point.y-rig.bodyOrigin[1])*rig.worldScale};}
