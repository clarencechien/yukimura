const $=s=>document.querySelector(s),frames=[...document.querySelectorAll('iframe')],views=[$('#before'),$('#after')];
let age=1180,playing=false,last,ready=false;
function stop(){playing=false;$('#play').textContent='播放（¼ 倍）';}
function draw(){
 if(!ready)return;
 const states=frames.map((frame,i)=>{const doc=frame.contentDocument,input=doc.querySelector('#time');input.value=age;input.dispatchEvent(new frame.contentWindow.Event('input'));const source=doc.querySelector('#view');views[i].getContext('2d').drawImage(source,600,330,600,260,0,0,600,260);return frame.contentWindow.freeArmSettle;});
 $('#age').textContent=`${age.toFixed(1)} ms`;$('#time').value=age;$('#status').textContent=age<=1200?'側倒之前：兩版相同。':'相同時間與上半身；右側護脛與靴保持原尺寸，在大腿後方連續滑出。';
 window.legReview={ready:true,age,playing,sourceAges:states.map(s=>s.age),legURLs:states.map(s=>s.rearLeg?.url??null),weaponEqual:JSON.stringify(states[0].swords)===JSON.stringify(states[1].swords),headEqual:JSON.stringify(states[0].helmet)===JSON.stringify(states[1].helmet),poseEqual:JSON.stringify(states[0].pose)===JSON.stringify(states[1].pose)};
}
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};
for(const b of document.querySelectorAll('[data-time]'))b.onclick=()=>{stop();age=Number(b.dataset.time);draw();};
$('#play').onclick=()=>{if(age>=1540)age=1180;playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':'播放（¼ 倍）';draw();};
document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined)age=Math.min(1540,age+Math.min(now-last,60)*.25);if(age>=1540)stop();draw();}last=now;requestAnimationFrame(tick);}
try{
 const start=performance.now();while(!frames.every(f=>f.contentWindow.freeArmSettle?.ready)){if(performance.now()-start>15000)throw Error('兩個版本未能完成載入，請重新整理。');await new Promise(r=>setTimeout(r,50));}
 ready=true;$('#controls').disabled=false;draw();requestAnimationFrame(tick);
}catch(e){$('#status').textContent=e.message;throw e;}
