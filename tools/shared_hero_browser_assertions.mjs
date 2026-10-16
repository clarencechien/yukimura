import fs from 'node:fs';
const rig=JSON.parse(fs.readFileSync(new URL('../docs/routes/jigoku-2d/combat/thrust-rig.json',import.meta.url)));
import assert from 'node:assert/strict';
// Reconstruct endpoints from actual Phaser texture dimensions/origin/angle.
// This does not simply trust the pose module's exported tip or length.
export function assertHeroWeapon(row,guardRig){
 const w=row.heroWeapon;
 assert.equal(w.visible,true);assert.equal(w.texture,'guardYari');
 assert.equal(row.texture,'hero-lower');
 const r=guardRig.weapon,p=w.pose,a=w.angle*Math.PI/180;
 const map=(x,y)=>{const dx=(x/r.sourceSize[0]-w.originX)*w.width,dy=(y/r.sourceSize[1]-w.originY)*w.height;return {x:w.x+dx*Math.cos(a)-dy*Math.sin(a),y:w.y+dx*Math.sin(a)+dy*Math.cos(a)};};
 const butt=map(r.axisLeft,r.axisY),tip=map(r.axisRight,r.axisY);
 assert.ok(Math.abs(Math.hypot(tip.x-butt.x,tip.y-butt.y)-760)<1e-6);
 const scale=760/(r.axisRight-r.axisLeft),rear=map(r.axisLeft+180/scale,r.axisY),front=map(r.axisLeft+417/scale,r.axisY);
 assert.ok(Math.hypot(rear.x-p.palms[0].x,rear.y-p.palms[0].y)<1e-6);
 assert.ok(Math.hypot(front.x-p.palms[1].x,front.y-p.palms[1].y)<1e-6);
 if(row.phase==='attack')assert.ok(Math.hypot(tip.x-row.collisionTip.x,tip.y-row.collisionTip.y)<1e-6,'Visible blade endpoint equals collision track');
 assert.ok(w.order>w.bodyOrder);
 const mapPart=(sprite,name,point)=>{
  const layer=rig.layers[name],a=sprite.angle*Math.PI/180;
  const x=((point[0]-layer.box[0])/layer.size[0]-sprite.originX)*sprite.width;
  const y=((point[1]-layer.box[1])/layer.size[1]-sprite.originY)*sprite.height;
  return {x:sprite.x+x*Math.cos(a)-y*Math.sin(a),y:sprite.y+x*Math.sin(a)+y*Math.cos(a)};
 };
 const near=(a,b)=>assert.ok(Math.hypot(a.x-b.x,a.y-b.y)<1e-5);
 for(let i=0;i<2;i++){
  const h=w.hands[i];assert.equal(h.visible,true);assert.ok(h.order>w.order);
  const side=i===0?'rear':'front',j=rig.joints[side],upper=row.heroParts[side+'Upper'],fore=row.heroParts[side+'Fore'];
  assert.equal(h.texture,'hero-'+side+'Hand');
  near(mapPart(row.heroParts.torso,'torso',j.shoulder),upper);
  near(mapPart(upper,side+'Upper',j.elbow),fore);
  near(mapPart(fore,side+'Fore',j.wrist),h);
  near(mapPart(h,side+'Hand',j.grip),p.palms[i]);
  assert.ok(Math.abs(Math.hypot(fore.x-upper.x,fore.y-upper.y)-Math.hypot(j.elbow[0]-j.shoulder[0],j.elbow[1]-j.shoulder[1]))<1e-5);
  assert.ok(Math.abs(Math.hypot(h.x-fore.x,h.y-fore.y)-Math.hypot(j.wrist[0]-j.elbow[0],j.wrist[1]-j.elbow[1]))<1e-5);
  for(const name of ['lower','torso',side+'Upper',side+'Fore']){
   const part=row.heroParts[name];assert.equal(part.visible,true);assert.equal(part.texture,'hero-'+name);assert.equal(part.width,rig.layers[name].size[0]);assert.equal(part.height,rig.layers[name].size[1]);
  }
  assert.ok(upper.order<row.heroParts.torso.order);assert.ok(fore.order>row.heroParts.torso.order);assert.ok(fore.order<w.order);
 }
 for(const [side,j] of Object.entries(rig.legs)){
  const thigh=row.heroParts[side+'Thigh'],shin=row.heroParts[side+'Shin'],foot=row.heroParts[side+'Foot'];
  near(mapPart(row.heroParts.lower,'lower',j.hip),thigh);
  near(mapPart(thigh,side+'Thigh',j.knee),shin);
  near(mapPart(shin,side+'Shin',j.ankle),foot);
  near(foot,{x:j.ankle[0]+35,y:j.ankle[1]+90});assert.equal(foot.angle,0);
  for(const name of [side+'Thigh',side+'Shin',side+'Foot']){
   const part=row.heroParts[name];assert.equal(part.visible,true);assert.equal(part.texture,'hero-'+name);
   assert.equal(part.width,rig.layers[name].size[0]);assert.equal(part.height,rig.layers[name].size[1]);
  }
  assert.ok(foot.order<shin.order);assert.ok(shin.order<thigh.order);assert.ok(thigh.order<row.heroParts.lower.order);
 }
 for(const [side,point] of [['rear',guardRig.poses[3].rearSole],['front',guardRig.poses[3].frontSole]])if(point)near(mapPart(row.heroParts[side+'Foot'],side+'Foot',point),{x:point[0]+35,y:point[1]+90});
}
