import {transitionPose} from '../free-arm-transition/rig.mjs';
import {settlePose} from './rig.mjs';
import {releasingSword} from './release.mjs';
import {yieldPose,YIELD} from './yield.mjs';
import {fallPose,fallSword} from './fall.mjs';
const baseline=new URLSearchParams(location.search).get('motion')==='baseline';
const $=s=>document.querySelector(s),canvas=$('#view'),ctx=canvas.getContext('2d');
let meta,kit,support,settle,swordRig,release,fall,images,swords,drawEvents,age=330,playing=false,last,records,bodies,bases,legs;
const load=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error('無法載入 '+src));im.src=src;});
const matrix=()=>{const {a,b,c,d,e,f}=ctx.getTransform();return {a,b,c,d,e,f};};
function body(name,p,panel){const m=meta.frames[p.index].parts[name],delta=name==='lower'?{x:0,y:0}:p.bodyOffset;ctx.save();ctx.translate(delta.x,delta.y);ctx.drawImage(images['old:'+m.url],m.box[0],m.box[1],m.box[2]-m.box[0],m.box[3]-m.box[1]);drawEvents.push({name,panel});bodies.push({name,panel,frame:p.index,offset:delta,transform:matrix(),box:m.box});ctx.restore();}
function part(t,panel){const m=t.name==='palm'?support.palm:kit.parts[t.name];ctx.save();ctx.translate(t.point.x,t.point.y);ctx.rotate(t.angle*Math.PI/180);ctx.drawImage(images[t.name],-m.pivot[0],-m.pivot[1],...m.displaySize);drawEvents.push({name:t.name,panel});records.push({name:t.name,panel,transform:matrix(),pivot:m.pivot,end:m.end??m.heel??null});ctx.restore();}
function hinged(name,p,panel){const m=settle.parts[name];ctx.save();ctx.translate(p.torso.pivot.x+p.torso.offset.x,p.torso.pivot.y+p.torso.offset.y);ctx.rotate(p.torso.angle*Math.PI/180);ctx.translate(-p.torso.pivot.x,-p.torso.pivot.y);ctx.drawImage(images['new:'+name],m.box[0],m.box[1],m.box[2]-m.box[0],m.box[3]-m.box[1]);drawEvents.push({name,panel});bodies.push({name,panel,url:m.url,mode:'hinge',transform:matrix(),box:m.box});ctx.restore();}
function lower(p,panel,name='lower'){const m=settle.parts[name];ctx.drawImage(images['new:'+name],m.box[0],m.box[1],m.box[2]-m.box[0],m.box[3]-m.box[1]);drawEvents.push({name,panel});bodies.push({name,panel,url:m.url,mode:'fixed',transform:matrix(),box:m.box});}
function leg(t,panel){const m=settle.parts[t.name];ctx.save();ctx.translate(t.point.x,t.point.y);ctx.rotate(t.angle*Math.PI/180);ctx.drawImage(images['new:'+t.name],-m.pivot[0],-m.pivot[1]);drawEvents.push({name:t.name,panel});legs.push({name:t.name,panel,transform:matrix(),pivot:m.pivot,end:m.end,alpha:ctx.globalAlpha,size:[images['new:'+t.name].width,images['new:'+t.name].height]});ctx.restore();}
function swordPart(name,point,angle){
 const m=swordRig.parts[name];ctx.save();ctx.translate(point.x,point.y);ctx.rotate(angle*Math.PI/180);
 ctx.drawImage(images['sword:'+name],-m.pivot[0],-m.pivot[1],...m.size);
 drawEvents.push({name:'sword:'+name,panel:1});swords.push({name,panel:1,point,angle,pivot:m.pivot,size:m.size,transform:matrix(),layer:'behind-body',alpha:ctx.globalAlpha});ctx.restore();
}
function sword(p){
 swordPart('upper',p.shoulder,p.upperAngle);swordPart('fore',p.elbow,p.foreAngle);
 swordPart('katana',p.grip,p.bladeAngle);swordPart(p.handState,p.wrist,p.handAngle);
}
function fallBody(name,p,panel){
 const m=fall.frames[p.fallFrame].parts[name],delta=name==='lower'?{x:0,y:0}:p.fallOffset;
 ctx.save();ctx.translate(delta.x,delta.y);ctx.drawImage(images['fall:'+m.url],m.box[0],m.box[1],m.box[2]-m.box[0],m.box[3]-m.box[1]);
 drawEvents.push({name,panel});bodies.push({name,panel,frame:p.fallFrame,url:m.url,mode:'fall',offset:delta,transform:matrix(),box:m.box});ctx.restore();
}
function draw(){
 if(!images)return;
 const basePose=settlePose(age,settle,meta,kit,support),pose=fallPose(age,settle,meta,kit,support,fall),old=transitionPose(age,meta,kit,support),weapon=fallSword(age,pose,settle,swordRig,releasingSword(age,basePose,settle,swordRig,release),yieldPose(age,settle,meta,kit,support),fall),stacked=innerWidth<650,w=stacked?600:1200,h=stacked?1440:720;
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 ctx.fillStyle='#19252c';ctx.fillRect(0,0,w,h);records=[];bodies=[];bases=[];legs=[];swords=[];drawEvents=[];
 for(let panel=0;panel<2;panel++){
  const p=panel?pose:old;
  ctx.save();ctx.translate(stacked?0:panel*600,stacked?panel*720:0);ctx.fillStyle='#e7d9bf';ctx.font='21px sans-serif';ctx.fillText(panel?(baseline?'原三格側倒':'低頭過渡・四格側倒'):'上一輪五姿勢・末段換圖',24,38);
  ctx.save();ctx.beginPath();ctx.rect(0,65,600,550);ctx.clip();ctx.translate(-50,-10);ctx.scale(.8,.8);bases.push(matrix());
  ctx.fillStyle='#101b21';ctx.beginPath();ctx.ellipse(610,686,190,26,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle=`rgba(0,0,0,${p.shadowAlpha})`;ctx.beginPath();ctx.ellipse(p.contact.x,p.contact.y+12,p.shadowWidth/2,6,0,0,Math.PI*2);ctx.fill();
  if(panel&&$('#sword').checked){if(!weapon.held){ctx.fillStyle=`rgba(0,0,0,${weapon.grounded ? .23 : .10})`;ctx.beginPath();ctx.ellipse((weapon.bounds.left+weapon.bounds.right)/2,release.groundY+4,(weapon.bounds.right-weapon.bounds.left)/2,5,0,0,Math.PI*2);ctx.fill();}sword(weapon);}
  if(panel&&p.fallFrame>=0){fallBody('lower',p,panel);fallBody('torso',p,panel);}
  else if(panel&&p.late){
   lower(p,panel,'restore');if(!$('#xray').checked)for(const t of p.leg.parts)leg(t,panel);lower(p,panel);hinged('torso',p,panel);lower(p,panel,'waist');if($('#xray').checked)for(const t of p.leg.parts)leg(t,panel);
  }else{body('lower',p,panel);body('torso',p,panel);}
  if($('#arm').checked){part(p.parts[0],panel);if($('#cap').checked){if(panel&&p.fallFrame>=0)fallBody('cap',p,panel);else if(panel&&p.late)hinged('cap',p,panel);else body('cap',p,panel);}part(p.parts[1],panel);part(p.parts[2],panel);}
  if(panel&&p.late&&!(p.fallFrame>=0)&&$('#patch').checked){ctx.strokeStyle='#f6bb6b';ctx.lineWidth=1.5;ctx.beginPath();settle.vacatedLegPolygon.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.closePath();ctx.stroke();ctx.strokeStyle='#8ee0c6';ctx.beginPath();settle.preservedKneePolygon.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.closePath();ctx.stroke();}
  if(panel&&p.late&&!(p.fallFrame>=0)&&$('#joints').checked){ctx.strokeStyle='#efb665';ctx.beginPath();[p.leg.knee,p.leg.ankle,p.leg.toe].forEach((q,i)=>i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y));ctx.stroke();for(const q of [p.leg.knee,p.leg.ankle,p.leg.toe])ctx.strokeRect(q.x-3,q.y-3,6,6);}

  if(panel&&$('#sword').checked&&$('#joints').checked){ctx.strokeStyle='#f4aa80';ctx.beginPath();[weapon.shoulder,weapon.elbow,weapon.wrist,weapon.grip].forEach((q,i)=>i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y));ctx.stroke();for(const q of [weapon.shoulder,weapon.elbow,weapon.wrist,weapon.grip])ctx.strokeRect(q.x-3,q.y-3,6,6);}
  if($('#joints').checked){ctx.strokeStyle='#8ee0c6';ctx.lineWidth=1.6;ctx.beginPath();[p.shoulder,p.elbow,p.wrist,p.heel].filter(Boolean).forEach((q,i)=>i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y));ctx.stroke();for(const q of [p.shoulder,p.elbow,p.wrist]){ctx.fillStyle='#f4e6bf';ctx.fillRect(q.x-3,q.y-3,6,6);}ctx.strokeStyle='#e9b260';ctx.strokeRect(p.contact.x-4,p.contact.y-4,8,8);if(p.index<4){const q=meta.frames[p.index].registration.frontSole;ctx.strokeRect(q[0]-4,q[1]-4,8,8);}}
  ctx.restore();ctx.fillStyle='#b9c9cd';ctx.font='18px sans-serif';ctx.fillText(panel&&p.late?(p.fallFrame>=0?({bridge:'低頭過渡',roll:'骨盆開始側移',side:'膝部翻落',rest:'側躺落定'})[fall.frames[p.fallFrame].id]:age>=YIELD.release?'撐掌離地・手臂收回':age>YIELD.start?'胸肩下降・掌根暫時固定':p.planted?'掌根固定・護脛與鞋收進衣甲後':'先伸手・前腳仍承接'):`${['蹲低','重心前移','後膝降低','近地','跪地'][p.index]}`,24,640);ctx.font='15px sans-serif';ctx.fillText(panel?(weapon.held?'遠側手持刀、近側撐地；刀柄鎖在握拳內':weapon.phase==='settled'?'刀留在原地；側倒原畫換姿，手臂共用':'鬆手後刀獨立下落；掌根仍固定'):'保留前輪末段突然收腳的行為供比較',24,673);ctx.restore();
 }
 $('#age').textContent=`${Math.round(age)} ms`;$('#time').value=age;$('#status').textContent=`${pose.late?'末段共用身體':'前段沿用原畫'}｜持刀側 ${$('#sword').checked?'已裝配':'隱藏'}｜${({held:'握刀',falling:'鬆手落刀',contact:'刀碰地轉平',settled:'刀已落定'})[weapon.phase]}｜側倒 ${Math.round((pose.fallProgress??0)*100)}%｜卸力 ${Math.round((pose.unload??0)*100)}%｜收腳 ${Math.round(pose.leg.progress*100)}%｜踝部相對轉角 ${pose.leg.ankleDeflection.toFixed(1)}°。`;
 window.freeArmSettle={ready:true,age,playing,pose,basePose,old,records,bodies,bases,legs,swords,drawEvents,weapon,swordRig,release,fall,swordVisible:$('#sword').checked,meta,kit,support,settle,xray:$('#xray').checked,armVisible:$('#arm').checked,capVisible:$('#cap').checked};
}
function stop(){playing=false;$('#play').textContent='播放';}
$('#play').onclick=()=>{if(age>=fall.reviewEnd)age=330;playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':'播放';draw();};
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};
for(const id of ['joints','arm','cap','xray','patch','sword'])$('#'+id).onchange=draw;
for(const [id,delta] of [['prev',-1],['next',1]])$('#'+id).onclick=()=>{stop();const keys=[330,352,376,400,420,440,460,480,500,540,600,700,860,930,1000,1090,1180,1220,1260,1380,1500,1800];age=delta>0?(keys.find(t=>t>age+.01)??fall.reviewEnd):([...keys].reverse().find(t=>t<age-.01)??330);draw();};
window.addEventListener('resize',draw);document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined){age=Math.min(fall.reviewEnd,age+Math.min(now-last,60)*Number($('#speed').value));if(age>=fall.reviewEnd)stop();}draw();}last=now;requestAnimationFrame(tick);}
try{const urls=['../free-arm-transition/transition.json','../free-arm-parts/parts.json','../free-arm-support/support.json','settle.json','../combat/enemy-rig.json','release.json',baseline?'fall.json':'bridge.json'];[meta,kit,support,settle,swordRig,release,fall]=await Promise.all(urls.map(async url=>{const r=await fetch(url);if(!r.ok)throw Error('無法載入 '+url);return r.json();}));const paths=[...new Set(meta.frames.flatMap(f=>Object.values(f.parts).map(p=>p.url)))];images=Object.fromEntries(await Promise.all([...fall.frames.flatMap(f=>Object.values(f.parts)).map(async p=>['fall:'+p.url,await load(p.url)]),...['upper','fore','grip','relax','open','katana'].map(async n=>['sword:'+n,await load(`../combat/enemy-${n}.webp`)]),...paths.map(async url=>['old:'+url,await load('../free-arm-transition/'+url)]),...Object.entries(settle.parts).map(async ([name,p])=>['new:'+name,await load(p.url)]),...['upper','fore','palm','open'].map(async n=>[n,await load(`../free-arm-${n==='palm'?'support':'parts'}/${n}.webp`)])]));$('#controls').disabled=false;draw();requestAnimationFrame(tick);}catch(e){$('#status').textContent=e.message;throw e;}
