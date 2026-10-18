const $=s=>document.querySelector(s),frames=[...document.querySelectorAll('iframe')],views=[$('#before'),$('#after')],feet=[$('#foot-before'),$('#foot-after')];
let age=1000,playing=false,last,ready=false;
const playLabel=()=>`播放（${Number($('#speed').value)===1?'原速':'¼ 倍'}）`;
function stop(){playing=false;$('#play').textContent=playLabel();}
function draw(){
 if(!ready)return;
 const states=frames.map((frame,i)=>{const doc=frame.contentDocument,input=doc.querySelector('#time');input.value=age;input.dispatchEvent(new frame.contentWindow.Event('input'));const source=doc.querySelector('#view');views[i].getContext('2d').drawImage(source,600,330,600,260,0,0,600,260);feet[i].getContext('2d').drawImage(source,890,370,225,180,0,0,450,360);return frame.contentWindow.freeArmSettle;});
 $('#age').textContent=`${age.toFixed(1)} ms`;$('#time').value=age;$('#status').textContent=age>1200&&age<=1440?'右側使用同組三姿勢；肩點沿原動作，身體微轉保持下緣貼地。':'兩版畫面相同；新稿只出現在 1200–1440 ms。';
 window.sequenceReview={ready:true,age,playing,sourceAges:states.map(s=>s.age),bodyURLs:states.map(s=>s.bodies.filter(b=>b.panel===1&&['lower','torso','body-core'].includes(b.name)).map(b=>b.url)),weaponEqual:JSON.stringify(states[0].swords)===JSON.stringify(states[1].swords),contact:states[1].sequenceBody??null,headEqual:JSON.stringify(states[0].helmet)===JSON.stringify(states[1].helmet),poseEqual:JSON.stringify(states[0].pose)===JSON.stringify(states[1].pose)};
}
$('#speed').onchange=()=>{last=undefined;$('#play').textContent=playing?'暫停':playLabel();draw();};
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};
for(const b of document.querySelectorAll('[data-time]'))b.onclick=()=>{stop();age=Number(b.dataset.time);draw();};
$('#play').onclick=()=>{if(age>=1500)age=1000;playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':playLabel();draw();};
document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined)age=Math.min(1500,age+Math.min(now-last,60)*Number($('#speed').value));if(age>=1500)stop();draw();}last=now;requestAnimationFrame(tick);}
try{
 const start=performance.now();while(!frames.every(f=>f.contentWindow.freeArmSettle?.ready)){if(performance.now()-start>15000)throw Error('兩個版本未能完成載入，請重新整理。');await new Promise(r=>setTimeout(r,50));}
 ready=true;$('#controls').disabled=false;draw();requestAnimationFrame(tick);
}catch(e){$('#status').textContent=e.message;throw e;}
