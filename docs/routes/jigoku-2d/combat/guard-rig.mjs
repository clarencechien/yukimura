// One rigid spear. Manually marked palm centers define its axis, never its length.
export function guardRigPose(pose,rig){
  if(pose===null)return null;
  return rigidSpearPose(rig.poses[pose],rig.weapon,pose);
}

export function rigidSpearPose(row,weapon,pose){
  const palms=row.grips.map(([x,y])=>({x:x+35,y:y+90}));
  const dx=palms[1].x-palms[0].x,dy=palms[1].y-palms[0].y,d=Math.hypot(dx,dy),ux=dx/d,uy=dy/d;
  const scale=weapon.length/(weapon.axisRight-weapon.axisLeft),rear=palms[0];
  const point=t=>({x:rear.x+ux*t,y:rear.y+uy*t});
  return {pose,palms,rear,front:point(weapon.gripDistance),butt:point(-weapon.rearGripFromButt),tip:point(weapon.length-weapon.rearGripFromButt),contact:point(310),angle:Math.atan2(dy,dx)*180/Math.PI,
    width:weapon.sourceSize[0]*scale,height:weapon.sourceSize[1]*scale,originX:(weapon.axisLeft+weapon.rearGripFromButt/scale)/weapon.sourceSize[0],originY:weapon.axisY/weapon.sourceSize[1],registrationError:Math.abs(d-weapon.gripDistance)};
}
