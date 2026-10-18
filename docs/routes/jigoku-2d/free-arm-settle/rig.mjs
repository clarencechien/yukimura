import {transitionPose} from '../free-arm-transition/rig.mjs';
const ease=t=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
export const rotate=(v,degrees)=>{const a=degrees*Math.PI/180;return {x:v.x*Math.cos(a)-v.y*Math.sin(a),y:v.x*Math.sin(a)+v.y*Math.cos(a)};};
export function settlePose(age,meta,transition,kit,support){
 const p=transitionPose(age,transition,kit,support),late=p.index>=3,u=Math.max(0,Math.min(1,(p.age-meta.foldStart)/(meta.foldEnd-meta.foldStart)));
 const shinAngle=meta.shinRotation*ease(u),shoeAngle=meta.shoeRotation*ease((u-.35)/.65);
 const knee={x:meta.knee[0],y:meta.knee[1]},v=rotate({x:meta.ankle[0]-knee.x,y:meta.ankle[1]-knee.y},shinAngle),ankle={x:knee.x+v.x,y:knee.y+v.y};
 const q=rotate({x:meta.toe[0]-meta.ankle[0],y:meta.toe[1]-meta.ankle[1]},shoeAngle),toe={x:ankle.x+q.x,y:ankle.y+q.y};
 const pivot={x:meta.hipPivot[0],y:meta.hipPivot[1]},from={x:meta.shoulder[0]-pivot.x,y:meta.shoulder[1]-pivot.y},to={x:p.shoulder.x-pivot.x,y:p.shoulder.y-pivot.y};
 const angle=(Math.atan2(to.y,to.x)-Math.atan2(from.y,from.x))*180/Math.PI,turned=rotate(from,angle);
 const torso=p.age<400?{pivot,angle:0,offset:{...p.bodyOffset}}:{pivot,angle,offset:{x:to.x-turned.x,y:to.y-turned.y}};
 return {...p,late,torso,leg:{knee,ankle,toe,shinAngle,shoeAngle,ankleDeflection:shoeAngle-shinAngle,progress:ease(u),parts:[{name:'shin',point:knee,angle:shinAngle},{name:'shoe',point:ankle,angle:shoeAngle}]}};
}
