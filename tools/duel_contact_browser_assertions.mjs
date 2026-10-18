import assert from 'node:assert/strict';import fs from 'node:fs';
const rig=JSON.parse(fs.readFileSync(new URL('../docs/routes/jigoku-2d/combat/enemy-rig.json',import.meta.url)));
const near=(a,b)=>assert.ok(Math.hypot(a.x-b.x,a.y-b.y)<1e-5,'Actual blade and shaft must share the contact');
function map(sprite,point,size){
 const a=sprite.angle*Math.PI/180,x=(point.x/size[0]-sprite.originX)*sprite.width,y=(point.y/size[1]-sprite.originY)*sprite.height;
 return {x:sprite.x+x*Math.cos(a)-y*Math.sin(a),y:sprite.y+x*Math.sin(a)+y*Math.cos(a)};
}
export function assertDuelContact(row,guardRig){
 const c=row.contact;if(!c)return;
 assert.equal(row.weapon.visible,true);assert.equal(row.weapon.held,true);
 assert.equal(row.weapon.width,rig.parts.katana.size[0]*rig.worldScale);
 assert.equal(row.weapon.height,rig.parts.katana.size[1]*rig.worldScale);
 const actual=map(row.weapon,c.mark,rig.parts.katana.size);near(actual,c.point);
 if(c.weight===1){
  const w=guardRig.weapon,scale=w.length/(w.axisRight-w.axisLeft);
  const pole=map(row.heroWeapon,{x:w.axisLeft+(w.rearGripFromButt+310)/scale,y:w.axisY},w.sourceSize);
  near(actual,pole);near(actual,c.target);
 }
 if(row.lastClash){near(row.lastClash.point,row.lastClash.target);assert.equal(row.lastClash.weight,1);}
}
