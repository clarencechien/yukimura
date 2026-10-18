import {MARKS,assess,shoulderPlan,trajectory} from './reach.mjs';
const $=s=>document.querySelector(s),canvas=$('#view'),ctx=canvas.getContext('2d');
const load=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error('無法載入 '+src));im.src=src;});
let atlas,candidate,playing=false,age=330,last;
const markFor=p=>p.frame===3?MARKS.buckle:p.frame===4?MARKS.crouch:useCandidate()?MARKS.candidate:MARKS.kneel;
const useCandidate=()=>$('#source').value==='candidate';
const circle=(p,color,r=5)=>{ctx.fillStyle=color;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();};
function line(points,color,width=4,dash=[]){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.setLineDash(dash);ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke();ctx.setLineDash([]);}
const toPoint=([x,y])=>({x,y});
function draw(){
 if(!atlas||!candidate)return;
 const pose=trajectory(age,{candidate:useCandidate()}),plan=trajectory(age,{planned:true,candidate:useCandidate()}),mark=markFor(pose);
 const stacked=innerWidth<650,w=stacked?440:1320,h=stacked?1680:560;
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
 ctx.fillStyle='#19252c';ctx.fillRect(0,0,w,h);ctx.font='20px sans-serif';ctx.textBaseline='top';
 for(let col=0;col<3;col++){
  ctx.save();ctx.translate(stacked?0:col*440,stacked?col*560:0);
  ctx.fillStyle='#e2d6bd';ctx.fillText(['原畫・人工關節標記','固定 85／90・紅線表示搆不到','降肩目標・需要配合重畫身體'][col],16,18);
  ctx.save();ctx.beginPath();ctx.rect(0,54,440,430);ctx.clip();ctx.translate(-200,-65);ctx.scale(.75,.75);
  ctx.globalAlpha=col===0?.85:.3;
  if(useCandidate()&&pose.frame===5)ctx.drawImage(candidate,0,0,1152,768);
  else ctx.drawImage(atlas,pose.frame%3*1152,Math.floor(pose.frame/3)*768,1152,768,0,0,1152,768);
  ctx.globalAlpha=1;
  if(col===0){const points=[mark.shoulder,mark.elbow,mark.wrist].map(toPoint);line(points,'#e9ba6c');points.forEach(p=>circle(p,'#f7cd86'));}
  else{
   const p=col===1?pose:plan,color=col===1&&!p.reachable?'#ff7c72':'#83d9bf';line([p.shoulder,p.elbow,p.wrist],color);[p.shoulder,p.elbow,p.wrist].forEach(q=>circle(q,color));circle(p.target,'#fff',3);
   if(p.miss>.01)line([p.wrist,p.target],'#ff7c72',3,[5,4]);
   if(col===2)line([pose.shoulder,plan.shoulder],'#dcc18d',2,[4,4]);
  }
  ctx.restore();ctx.fillStyle='#b7c7cc';ctx.font='18px sans-serif';ctx.fillText(col===0?['屈膝','蹲低','跪下'][pose.frame-3]:col===1?`腕目標差距 ${pose.miss.toFixed(1)} px`:`肩下降 ${(plan.shoulder.y-pose.shoulder.y).toFixed(1)} px`,16,505);ctx.restore();
 }
 $('#age').textContent=`${Math.round(age)} ms`;
 $('#status').textContent=`${useCandidate()?'未採用試修稿':'現行原畫'}｜肩腕距離 ${pose.distance.toFixed(1)} px；${pose.reachable?'此時候選固定臂長可達':'此時超出候選固定臂長'}。綠色骨架可達，不代表人物原畫已隨骨架修正。`;
 window.freeArmReview={ready:true,age,candidate:useCandidate(),playing,pose,plan,marks:MARKS};
}
function table(){
 $('#measurements').replaceChildren(...Object.entries(MARKS).map(([name,m])=>{const a=assess(m),p=shoulderPlan(m),tr=document.createElement('tr');for(const value of [{buckle:'屈膝',crouch:'蹲低',kneel:'現行跪地',candidate:'試修跪地'}[name],a.distance.toFixed(1)+' px',a.overreach.toFixed(1)+' px',p.lowering.toFixed(1)+' px']){const td=document.createElement('td');td.textContent=value;tr.append(td);}return tr;}));
}
function stop(){playing=false;$('#play').textContent='播放試算 ×¼';}
$('#play').onclick=()=>{playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':'播放試算 ×¼';draw();};
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};
$('#source').onchange=()=>draw();window.addEventListener('resize',()=>{if(atlas)draw();});document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined){age+=Math.min(now-last,60)/4;if(age>420)age=180;$('#time').value=age;}draw();}last=now;requestAnimationFrame(tick);}
try{[atlas,candidate]=await Promise.all([load('../combat/ghost-warrior-hd.webp'),load('candidate.webp')]);table();$('#controls').disabled=false;draw();requestAnimationFrame(tick);}catch(e){$('#status').textContent=e.message;}
