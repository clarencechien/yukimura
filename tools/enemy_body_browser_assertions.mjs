import assert from 'node:assert/strict';
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-5,`${a} != ${b}`);
export function assertEnemyBody(row){
 const parts=row.enemyBodyParts,shared=!!row.enemyBodyPose,visible=row.targetKind==='warrior';
 assert.equal(row.legacyBodyVisible,visible&&!shared);
 for(const p of Object.values(parts))assert.equal(p.visible,visible&&shared);
 if(!shared)return;
 const torso=parts.torso,lower=parts.lower;
 near(torso.width,285*.6);near(torso.height,305*.6);
 near(lower.width,490*.6);near(lower.height,350*.6);near(lower.angle,0);
 // Independently map the painted socket through the ACTUAL Phaser transform.
 const x=((481-425)/285-torso.originX)*torso.width,y=((270-115)/305-torso.originY)*torso.height,a=torso.angle*Math.PI/180;
 near(torso.x+x*Math.cos(a)-y*Math.sin(a),row.renderedArm.shoulder.x);
 near(torso.y+x*Math.sin(a)+y*Math.cos(a),row.renderedArm.shoulder.y);
 near(lower.x,row.target.x+.6);near(lower.y,389.2);
 near(torso.x,lower.x);near(torso.y,lower.y);
 assert.ok(row.armOrder.upper<torso.order&&row.armOrder.upper>lower.order);
 assert.ok(row.armOrder.fore>torso.order&&row.armOrder.hand>row.armOrder.fore);
}
