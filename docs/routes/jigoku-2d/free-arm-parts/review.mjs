import {fittedArm} from './rig.mjs';
const $=s=>document.querySelector(s),canvas=$('#view'),ctx=canvas.getContext('2d');
let meta,images,age=250,playing=false,last,records=[];
const load=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error('無法載入 '+src));im.src=src;});
const matrix=()=>{const {a,b,c,d,e,f}=ctx.getTransform();return {a,b,c,d,e,f};};
function part(t,panel){const m=meta.parts[t.name];ctx.save();ctx.translate(t.point.x,t.point.y);ctx.rotate(t.angle*Math.PI/180);const transform=matrix();ctx.drawImage(images[t.name],-m.pivot[0],-m.pivot[1],...m.displaySize);records.push({name:t.name,panel,transform,pivot:m.pivot,end:m.end,displaySize:m.displaySize});ctx.restore();}
function skeleton(p){ctx.strokeStyle='#8ee0c6';ctx.lineWidth=1.5;ctx.beginPath();[p.shoulder,p.elbow,p.wrist].forEach((q,i)=>i?ctx.lineTo(q.x,q.y):ctx.moveTo(q.x,q.y));ctx.stroke();for(const q of [p.shoulder,p.elbow,p.wrist]){ctx.fillStyle='#f4e6bf';ctx.beginPath();ctx.arc(q.x,q.y,3,0,Math.PI*2);ctx.fill();}}
function draw(){
 if(!images)return;
 const p=fittedArm(age,meta,$('#hand').value),stacked=innerWidth<650,w=stacked?600:1200,h=stacked?1320:660;
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 ctx.fillStyle='#19252c';ctx.fillRect(0,0,w,h);records=[];const bases=[];
 for(let i=0;i<2;i++){
  ctx.save();ctx.translate(stacked?0:i*600,stacked?i*660:0);ctx.fillStyle='#e7d9bf';ctx.font='21px sans-serif';ctx.fillText(i?'部件放大・固定長度與腕角':'固定蹲姿試裝・伸手預備',24,38);
  ctx.save();ctx.beginPath();ctx.rect(0,60,600,530);ctx.clip();
  if(i===0){ctx.translate(-200,-100);ctx.scale(.95,.95);}else{ctx.translate(300,125);ctx.scale(2,2);ctx.translate(-p.shoulder.x,-p.shoulder.y);}
  bases.push(matrix());
  if(i===0)ctx.drawImage(images.body,0,0,1152,768);
  if($('#arm').checked){part(p.parts[0],i);
   if(i===0&&$('#cap').checked){const [x,y,r,b]=meta.cap.box;ctx.drawImage(images.cap,x,y,r-x,b-y);}
   part(p.parts[1],i);part(p.parts[2],i);
  }
  if($('#joints').checked)skeleton(p);
  ctx.restore();ctx.font='18px sans-serif';ctx.fillStyle='#b9c9cd';ctx.fillText(i?'上臂 85 px／前臂 90 px・腕部跟隨前臂':'同一張底圖；身體、腳位與肩甲保持不動',24,622);ctx.restore();
 }
 $('#age').textContent=`${Math.round(age)} ms`;$('#status').textContent=`${p.hand==='relax'?'半握':'張掌'}｜兩段長度固定，肩點固定。張掌仍有換圖感，胸甲與肩甲邊緣仍需精修。`;
 window.freeArmParts={ready:true,age,playing,pose:p,records,bases,meta,armVisible:$('#arm').checked,capVisible:$('#cap').checked};
}
function stop(){playing=false;$('#play').textContent='播放 ×¼';}
$('#play').onclick=()=>{playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':'播放 ×¼';draw();};
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};for(const id of ['hand','joints','arm','cap'])$('#'+id).onchange=draw;
window.addEventListener('resize',draw);document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined){age+=Math.min(now-last,60)/4;if(age>420)age=180;$('#time').value=age;}draw();}last=now;requestAnimationFrame(tick);}
try{const response=await fetch('parts.json');if(!response.ok)throw Error('無法載入部件資料');meta=await response.json();const entries=await Promise.all(['body','cap',...Object.keys(meta.parts)].map(async n=>[n,await load(n+'.webp')]));images=Object.fromEntries(entries);$('#controls').disabled=false;draw();requestAnimationFrame(tick);}catch(e){$('#status').textContent=e.message;}
