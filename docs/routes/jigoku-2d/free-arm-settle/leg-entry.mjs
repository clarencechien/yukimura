const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
export function legEntryPose(age,meta){
 if(!Number.isFinite(age))throw Error('finite age required');
 const progress=ease((age-meta.start)/(meta.end-meta.start));
 return {point:{x:meta.calf.pivot[0]+meta.target.offset[0]*progress,y:meta.calf.pivot[1]+meta.target.offset[1]*progress},angle:meta.target.angle*progress,progress};
}
