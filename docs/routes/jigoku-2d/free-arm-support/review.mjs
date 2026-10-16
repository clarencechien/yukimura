import {supportPose} from './rig.mjs';
const $=s=>document.querySelector(s),canvas=$('#view'),ctx=canvas.getContext('2d');
let meta,kit,images,age=420,playing=false,last,records=[],shadows=[],bodies=[];
const load=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error('無法載入 '+src));im.src=src;});
const matrix=()=>{const {a,b,c,d,e,f}=ctx.getTransform();return {a,b,c,d,e,f};};
function part(t,panel){const m=t.name==='palm'?meta.palm:kit.parts[t.name];ctx.save();ctx.translate(t.point.x,t.point.y);ctx.rotate(t.angle*Math.PI/180);ctx.drawImage(images[t.name],-m.pivot[0],-m.pivot[1],...m.displaySize);records.push({name:t.name,panel,transform:matrix(),pivot:m.pivot,end:m.end??m.heel,displaySize:m.displaySize});ctx.restore();}
function body(name,dy){const [x,y,r,b]=meta.body.boxes[name];ctx.save();ctx.translate(0,dy);ctx.drawImage(images[name],x,y,r-x,b-y);bodies.push({name,dy,transform:matrix(),box:meta.body.boxes[name]});ctx.restore();}
function skeleton(p){ctx.strokeStyle='#8ee0c6';ctx.lineWidth=1.5;ctx.beginPath();[p.shoulder,p.elbow,p.wrist,p.heel].forEach((q,i)=>i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y));ctx.stroke();for(const q of [p.shoulder,p.elbow,p.wrist,p.heel]){ctx.fillStyle='#f4e6bf';ctx.beginPath();ctx.arc(q.x,q.y,3,0,Math.PI*2);ctx.fill();}}
function draw(){
 if(!images)return;
 const p=supportPose(age,meta),stacked=innerWidth<650,w=stacked?600:1200,h=stacked?1320:660;
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 ctx.fillStyle='#19252c';ctx.fillRect(0,0,w,h);records=[];shadows=[];bodies=[];const bases=[];
 for(let i=0;i<2;i++){
  ctx.save();ctx.translate(stacked?0:i*600,stacked?i*660:0);ctx.fillStyle='#e7d9bf';ctx.font='21px sans-serif';ctx.fillText(i?'掌根固定・腕角與屈肘放大':'跪姿接地・肩胸下沉承力',24,38);
  ctx.save();ctx.beginPath();ctx.rect(0,60,600,530);ctx.clip();
  if(i===0){ctx.translate(-200,-100);ctx.scale(.95,.95);}else{ctx.translate(300,110);ctx.scale(2,2);ctx.translate(-meta.body.shoulder[0],-meta.body.shoulder[1]);}
  bases.push(matrix());
  const shadow={x:p.contact.x,y:p.contact.y+12,width:p.shadowWidth,height:12,alpha:p.shadowAlpha};ctx.fillStyle=`rgba(0,0,0,${shadow.alpha})`;ctx.beginPath();ctx.ellipse(shadow.x,shadow.y,shadow.width/2,shadow.height/2,0,0,Math.PI*2);ctx.fill();shadows.push({...shadow,panel:i,transform:matrix()});
  if(i===0){body('lower',0);body('torso',p.chestY);}
  if($('#arm').checked){part(p.parts[0],i);if(i===0&&$('#cap').checked)body('cap',p.chestY);part(p.parts[1],i);part(p.parts[2],i);}
  if($('#joints').checked){skeleton(p);ctx.strokeStyle='#ebae61';ctx.lineWidth=1;ctx.strokeRect(p.contact.x-4,p.contact.y-4,8,8);}
  ctx.restore();ctx.font='18px sans-serif';ctx.fillStyle='#b9c9cd';ctx.fillText(i?`腕部投影偏轉 ${Math.abs(p.wristDeflection).toFixed(1)}°`:(p.planted?'掌根定點・膝腳不動・肩胸繼續下降':'伸手接近地面・尚未承力'),24,622);ctx.restore();
 }
 $('#age').textContent=`${Math.round(age)} ms`;$('#status').textContent=`${p.planted?'掌根已固定':'接地前'}｜肩胸位移 ${p.chestY.toFixed(1)} px；臂長 85／90 px。腰部遮擋與掌根標記仍屬人工試裝。`;
 window.freeArmSupport={ready:true,age,playing,pose:p,records,bases,shadows,bodies,meta,kit,armVisible:$('#arm').checked,capVisible:$('#cap').checked};
}
function stop(){playing=false;$('#play').textContent='播放 ×¼';}
$('#play').onclick=()=>{playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':'播放 ×¼';draw();};
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};for(const id of ['joints','arm','cap'])$('#'+id).onchange=draw;
window.addEventListener('resize',draw);document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined){age+=Math.min(now-last,60)/4;if(age>540)age=330;$('#time').value=age;}draw();}last=now;requestAnimationFrame(tick);}
try{const [m,k]=await Promise.all([fetch('support.json'),fetch('../free-arm-parts/parts.json')]);if(!m.ok||!k.ok)throw Error('無法載入部件資料');meta=await m.json();kit=await k.json();images=Object.fromEntries(await Promise.all(['torso','lower','cap','palm','upper','fore'].map(async n=>[n,await load(['upper','fore'].includes(n)?'../free-arm-parts/'+n+'.webp':n+'.webp')])));$('#controls').disabled=false;draw();requestAnimationFrame(tick);}catch(e){$('#status').textContent=e.message;}
