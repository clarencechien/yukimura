const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
// Let the hanging plate rotate separately after the supporting hand is released.
// No state accumulation: reverse seeking uses the same shoulder and torso pose.
export function shoulderEntryPose(age,pose,meta){
 if(!Number.isFinite(age))throw Error('finite age required');
 const progress=ease((age-meta.start)/(meta.end-meta.start));
 const offset={x:meta.target.offset[0]*progress,y:meta.target.offset[1]*progress};
 return {point:{x:pose.shoulder.x+offset.x,y:pose.shoulder.y+offset.y},angle:pose.torso.angle+(meta.target.angle-pose.torso.angle)*progress,offset,progress};
}
