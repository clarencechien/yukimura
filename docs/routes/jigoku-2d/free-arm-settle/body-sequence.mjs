// A rigid body follows the existing shoulder while its lowest visible cell touches ground.
// This is a projected support constraint, not a simulation of knee or hip anatomy.
export function sequenceBodyPose(shoulder,frame,meta){
 if(!Number.isFinite(shoulder?.x)||!Number.isFinite(shoulder?.y))throw Error('finite shoulder required');
 const [px,py]=frame.pivot,rad=Math.PI/180;
 const support=angle=>{const c=Math.cos(angle*rad),s=Math.sin(angle*rad);return Math.max(...frame.supportHull.map(([x,y])=>(x-px)*s+(y-py)*c));};
 const target=meta.groundY-shoulder.y;let low=-meta.rotationLimit,high=meta.rotationLimit;
 // Authored hulls have their contact points to the right of the shoulder. Validate
 // monotonicity in tests; reject an unreachable contact instead of hiding it.
 if(target<support(low)||target>support(high))throw Error('body ground contact outside rotation range');
 for(let i=0;i<28;i++){const mid=(low+high)/2;if(support(mid)<target)low=mid;else high=mid;}
 const angle=(low+high)/2,c=Math.cos(angle*rad),s=Math.sin(angle*rad),vertices=frame.supportHull.map(([x,y])=>({x:shoulder.x+(x-px)*c-(y-py)*s,y:shoulder.y+(x-px)*s+(y-py)*c}));
 return {point:{...shoulder},angle,bounds:{left:Math.min(...vertices.map(p=>p.x)),right:Math.max(...vertices.map(p=>p.x)),top:Math.min(...vertices.map(p=>p.y)),bottom:Math.max(...vertices.map(p=>p.y))}};
}
