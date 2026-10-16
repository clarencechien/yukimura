import {transitionPose} from '../free-arm-transition/rig.mjs';
import {settlePose} from './rig.mjs';
const $=s=>document.querySelector(s),canvas=$('#view'),ctx=canvas.getContext('2d');
let meta,kit,support,settle,images,age=330,playing=false,last,records,bodies,bases,legs;
const load=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error('無法載入 '+src));im.src=src;});
const matrix=()=>{const {a,b,c,d,e,f}=ctx.getTransform();return {a,b,c,d,e,f};};
function body(name,p,panel){const m=meta.frames[p.index].parts[name],delta=name==='lower'?{x:0,y:0}:p.bodyOffset;ctx.save();ctx.translate(delta.x,delta.y);ctx.drawImage(images['old:'+m.url],m.box[0],m.box[1],m.box[2]-m.box[0],m.box[3]-m.box[1]);bodies.push({name,panel,frame:p.index,offset:delta,transform:matrix(),box:m.box});ctx.restore();}
function part(t,panel){const m=t.name==='palm'?support.palm:kit.parts[t.name];ctx.save();ctx.translate(t.point.x,t.point.y);ctx.rotate(t.angle*Math.PI/180);ctx.drawImage(images[t.name],-m.pivot[0],-m.pivot[1],...m.displaySize);records.push({name:t.name,panel,transform:matrix(),pivot:m.pivot,end:m.end??m.heel});ctx.restore();}
function hinged(name,p,panel){const m=settle.parts[name];ctx.save();ctx.translate(p.torso.pivot.x+p.torso.offset.x,p.torso.pivot.y+p.torso.offset.y);ctx.rotate(p.torso.angle*Math.PI/180);ctx.translate(-p.torso.pivot.x,-p.torso.pivot.y);ctx.drawImage(images['new:'+name],m.box[0],m.box[1],m.box[2]-m.box[0],m.box[3]-m.box[1]);bodies.push({name,panel,url:m.url,mode:'hinge',transform:matrix(),box:m.box});ctx.restore();}
function lower(p,panel,name='lower'){const m=settle.parts[name];ctx.drawImage(images['new:'+name],m.box[0],m.box[1],m.box[2]-m.box[0],m.box[3]-m.box[1]);bodies.push({name,panel,url:m.url,mode:'fixed',transform:matrix(),box:m.box});}
function leg(t,panel){const m=settle.parts[t.name];ctx.save();ctx.translate(t.point.x,t.point.y);ctx.rotate(t.angle*Math.PI/180);ctx.drawImage(images['new:'+t.name],-m.pivot[0],-m.pivot[1]);legs.push({name:t.name,panel,transform:matrix(),pivot:m.pivot,end:m.end,alpha:ctx.globalAlpha,size:[images['new:'+t.name].width,images['new:'+t.name].height]});ctx.restore();}
function draw(){
 if(!images)return;
 const pose=settlePose(age,settle,meta,kit,support),old=transitionPose(age,meta,kit,support),stacked=innerWidth<650,w=stacked?600:1200,h=stacked?1440:720;
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 ctx.fillStyle='#19252c';ctx.fillRect(0,0,w,h);records=[];bodies=[];bases=[];legs=[];
 for(let panel=0;panel<2;panel++){
  const p=panel?pose:old;
  ctx.save();ctx.translate(stacked?0:panel*600,stacked?panel*720:0);ctx.fillStyle='#e7d9bf';ctx.font='21px sans-serif';ctx.fillText(panel?'原圖膝甲共用・接續收腳':'上一輪五姿勢・末段換圖',24,38);
  ctx.save();ctx.beginPath();ctx.rect(0,65,600,550);ctx.clip();ctx.translate(-250,-90);ctx.scale(.95,.95);bases.push(matrix());
  ctx.fillStyle='#101b21';ctx.beginPath();ctx.ellipse(610,686,230,26,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle=`rgba(0,0,0,${p.shadowAlpha})`;ctx.beginPath();ctx.ellipse(p.contact.x,p.contact.y+12,p.shadowWidth/2,6,0,0,Math.PI*2);ctx.fill();
  if(panel&&p.late){
   lower(p,panel,'restore');if(!$('#xray').checked)for(const t of p.leg.parts)leg(t,panel);lower(p,panel);hinged('torso',p,panel);lower(p,panel,'waist');if($('#xray').checked)for(const t of p.leg.parts)leg(t,panel);
  }else{body('lower',p,panel);body('torso',p,panel);}
  if($('#arm').checked){part(p.parts[0],panel);if($('#cap').checked){if(panel&&p.late)hinged('cap',p,panel);else body('cap',p,panel);}part(p.parts[1],panel);part(p.parts[2],panel);}
  if(panel&&p.late&&$('#patch').checked){ctx.strokeStyle='#f6bb6b';ctx.lineWidth=1.5;ctx.beginPath();settle.vacatedLegPolygon.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.closePath();ctx.stroke();ctx.strokeStyle='#8ee0c6';ctx.beginPath();settle.preservedKneePolygon.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.closePath();ctx.stroke();}
  if(panel&&p.late&&$('#joints').checked){ctx.strokeStyle='#efb665';ctx.beginPath();[p.leg.knee,p.leg.ankle,p.leg.toe].forEach((q,i)=>i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y));ctx.stroke();for(const q of [p.leg.knee,p.leg.ankle,p.leg.toe])ctx.strokeRect(q.x-3,q.y-3,6,6);}

  if($('#joints').checked){ctx.strokeStyle='#8ee0c6';ctx.lineWidth=1.6;ctx.beginPath();[p.shoulder,p.elbow,p.wrist,p.heel].forEach((q,i)=>i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y));ctx.stroke();for(const q of [p.shoulder,p.elbow,p.wrist]){ctx.fillStyle='#f4e6bf';ctx.fillRect(q.x-3,q.y-3,6,6);}ctx.strokeStyle='#e9b260';ctx.strokeRect(p.contact.x-4,p.contact.y-4,8,8);if(p.index<4){const q=meta.frames[p.index].registration.frontSole;ctx.strokeRect(q[0]-4,q[1]-4,8,8);}}
  ctx.restore();ctx.fillStyle='#b9c9cd';ctx.font='18px sans-serif';ctx.fillText(panel&&p.late?(p.planted?'掌根固定・護脛與鞋收進衣甲後':'先伸手・前腳仍承接'):`${['蹲低','重心前移','後膝降低','近地','跪地'][p.index]}`,24,640);ctx.font='15px sans-serif';ctx.fillText(panel?'近地起共用原膝甲／腰帶；400 ms 不換下身':'保留前輪末段突然收腳的行為供比較',24,673);ctx.restore();
 }
 $('#age').textContent=`${Math.round(age)} ms`;$('#time').value=age;$('#status').textContent=`${pose.late?'末段共用身體':'前段沿用原畫'}｜收腳 ${Math.round(pose.leg.progress*100)}%｜踝部相對轉角 ${pose.leg.ankleDeflection.toFixed(1)}°。`;
 window.freeArmSettle={ready:true,age,playing,pose,old,records,bodies,bases,legs,meta,kit,support,settle,xray:$('#xray').checked,armVisible:$('#arm').checked,capVisible:$('#cap').checked};
}
function stop(){playing=false;$('#play').textContent='播放';}
$('#play').onclick=()=>{if(age>=540)age=330;playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':'播放';draw();};
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};
for(const id of ['joints','arm','cap','xray','patch'])$('#'+id).onchange=draw;
for(const [id,delta] of [['prev',-1],['next',1]])$('#'+id).onclick=()=>{stop();const keys=[330,352,376,400,420,440,460,480,500,540];age=delta>0?(keys.find(t=>t>age+.01)??540):([...keys].reverse().find(t=>t<age-.01)??330);draw();};
window.addEventListener('resize',draw);document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined){age=Math.min(540,age+Math.min(now-last,60)*Number($('#speed').value));if(age>=540)stop();}draw();}last=now;requestAnimationFrame(tick);}
try{const urls=['../free-arm-transition/transition.json','../free-arm-parts/parts.json','../free-arm-support/support.json','settle.json'];[meta,kit,support,settle]=await Promise.all(urls.map(async url=>{const r=await fetch(url);if(!r.ok)throw Error('無法載入 '+url);return r.json();}));const paths=[...new Set(meta.frames.flatMap(f=>Object.values(f.parts).map(p=>p.url)))];images=Object.fromEntries(await Promise.all([...paths.map(async url=>['old:'+url,await load('../free-arm-transition/'+url)]),...Object.entries(settle.parts).map(async ([name,p])=>['new:'+name,await load(p.url)]),...['upper','fore','palm'].map(async n=>[n,await load(`../free-arm-${n==='palm'?'support':'parts'}/${n}.webp`)])]));$('#controls').disabled=false;draw();requestAnimationFrame(tick);}catch(e){$('#status').textContent=e.message;throw e;}
