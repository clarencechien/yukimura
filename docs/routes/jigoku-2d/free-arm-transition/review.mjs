import {transitionPose,endpointPose} from './rig.mjs';
const $=s=>document.querySelector(s),canvas=$('#view'),ctx=canvas.getContext('2d');
let meta,kit,support,images,age=330,playing=false,last,records,bodies,bases;
const load=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error('無法載入 '+src));im.src=src;});
const matrix=()=>{const {a,b,c,d,e,f}=ctx.getTransform();return {a,b,c,d,e,f};};
function body(name,p,panel){const m=meta.frames[p.index].parts[name],delta=name==='lower'?{x:0,y:0}:p.bodyOffset;ctx.save();ctx.translate(delta.x,delta.y);ctx.drawImage(images[m.url],m.box[0],m.box[1],m.box[2]-m.box[0],m.box[3]-m.box[1]);bodies.push({name,panel,frame:p.index,offset:delta,transform:matrix(),box:m.box});ctx.restore();}
function part(t,panel){const m=t.name==='palm'?support.palm:kit.parts[t.name];ctx.save();ctx.translate(t.point.x,t.point.y);ctx.rotate(t.angle*Math.PI/180);ctx.drawImage(images[t.name],-m.pivot[0],-m.pivot[1],...m.displaySize);records.push({name:t.name,panel,transform:matrix(),pivot:m.pivot,end:m.end??m.heel});ctx.restore();}
function draw(){
 if(!images)return;
 const pose=transitionPose(age,meta,kit,support),old=endpointPose(age,meta,kit,support),stacked=innerWidth<650,w=stacked?600:1200,h=stacked?1440:720;
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 ctx.fillStyle='#19252c';ctx.fillRect(0,0,w,h);records=[];bodies=[];bases=[];
 for(let panel=0;panel<2;panel++){
  const p=panel?pose:old;
  ctx.save();ctx.translate(stacked?0:panel*600,stacked?panel*720:0);ctx.fillStyle='#e7d9bf';ctx.font='21px sans-serif';ctx.fillText(panel?'加入三張過渡格・共用手臂':'兩端直接切換・比較基準',24,38);
  ctx.save();ctx.beginPath();ctx.rect(0,65,600,550);ctx.clip();ctx.translate(-250,-90);ctx.scale(.95,.95);bases.push(matrix());
  ctx.fillStyle='#101b21';ctx.beginPath();ctx.ellipse(610,686,230,26,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle=`rgba(0,0,0,${p.shadowAlpha})`;ctx.beginPath();ctx.ellipse(p.contact.x,p.contact.y+12,p.shadowWidth/2,6,0,0,Math.PI*2);ctx.fill();
  body('lower',p,panel);body('torso',p,panel);
  if($('#arm').checked){part(p.parts[0],panel);if($('#cap').checked)body('cap',p,panel);part(p.parts[1],panel);part(p.parts[2],panel);}
  if($('#joints').checked){ctx.strokeStyle='#8ee0c6';ctx.lineWidth=1.6;ctx.beginPath();[p.shoulder,p.elbow,p.wrist,p.heel].forEach((q,i)=>i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y));ctx.stroke();for(const q of [p.shoulder,p.elbow,p.wrist]){ctx.fillStyle='#f4e6bf';ctx.fillRect(q.x-3,q.y-3,6,6);}ctx.strokeStyle='#e9b260';ctx.strokeRect(p.contact.x-4,p.contact.y-4,8,8);if(p.index<4){const q=meta.frames[p.index].registration.frontSole;ctx.strokeRect(q[0]-4,q[1]-4,8,8);}}
  ctx.restore();ctx.fillStyle='#b9c9cd';ctx.font='18px sans-serif';ctx.fillText(`${['蹲低','重心前移','後膝降低','近地','跪地'][p.index]}${p.planted?'・掌根固定':''}`,24,640);ctx.font='15px sans-serif';ctx.fillText(panel?'關鍵格換圖；肩胸平移，不扭曲人物網格':'僅用相同起終姿勢；不是上一版遊戲錄影',24,673);ctx.restore();
 }
 $('#age').textContent=`${Math.round(age)} ms`;$('#time').value=age;$('#status').textContent=`第 ${pose.index+1}／5 姿勢｜${pose.planted?'接地後掌根固定':'接地前'}｜腕部投影偏轉 ${Math.abs(pose.wristDeflection).toFixed(1)}°。`;
 window.freeArmTransition={ready:true,age,playing,pose,old,records,bodies,bases,meta,kit,support,armVisible:$('#arm').checked,capVisible:$('#cap').checked};
}
function stop(){playing=false;$('#play').textContent='播放';}
$('#play').onclick=()=>{if(age>=540)age=330;playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':'播放';draw();};
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};
for(const id of ['joints','arm','cap'])$('#'+id).onchange=draw;
for(const [id,delta] of [['prev',-1],['next',1]])$('#'+id).onclick=()=>{stop();const keys=[330,352,376,400,420,500,540];age=delta>0?(keys.find(t=>t>age+.01)??540):([...keys].reverse().find(t=>t<age-.01)??330);draw();};
window.addEventListener('resize',draw);document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined){age=Math.min(540,age+Math.min(now-last,60)*Number($('#speed').value));if(age>=540)stop();}draw();}last=now;requestAnimationFrame(tick);}
try{const urls=['transition.json','../free-arm-parts/parts.json','../free-arm-support/support.json'];[meta,kit,support]=await Promise.all(urls.map(async url=>{const r=await fetch(url);if(!r.ok)throw Error('無法載入 '+url);return r.json();}));const paths=[...new Set(meta.frames.flatMap(f=>Object.values(f.parts).map(p=>p.url)))];images=Object.fromEntries(await Promise.all([...paths.map(async url=>[url,await load(url)]),...['upper','fore','palm'].map(async n=>[n,await load(`../free-arm-${n==='palm'?'support':'parts'}/${n}.webp`)])]));$('#controls').disabled=false;draw();requestAnimationFrame(tick);}catch(e){$('#status').textContent=e.message;throw e;}
