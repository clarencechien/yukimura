const $=s=>document.querySelector(s),frames=[...document.querySelectorAll('iframe')],views=[$('#before'),$('#after')];
let age=960,playing=false,last,ready=false;
function stop(){playing=false;$('#play').textContent='播放（¼ 倍）';}
function draw(){
 if(!ready)return;
 const states=frames.map((frame,i)=>{const doc=frame.contentDocument,input=doc.querySelector('#time');input.value=age;input.dispatchEvent(new frame.contentWindow.Event('input'));const source=doc.querySelector('#view');views[i].getContext('2d').drawImage(source,600,330,600,260,0,0,600,260);return frame.contentWindow.freeArmSettle;});
 $('#age').textContent=`${age.toFixed(1)} ms`;$('#time').value=age;$('#status').textContent=age<1000?'離掌之前：兩版相同。':'相同時間、骨架與頭盔；右側讓肩甲先轉落，1200 ms 後回到前輪畫面。';
 window.entryReview={ready:true,age,playing,sourceAges:states.map(s=>s.age),entryURLs:states.map(s=>s.entryCap?.url??null),headEqual:JSON.stringify(states[0].helmet)===JSON.stringify(states[1].helmet),poseEqual:JSON.stringify(states[0].pose)===JSON.stringify(states[1].pose)};
}
$('#time').oninput=()=>{stop();age=Number($('#time').value);draw();};
for(const b of document.querySelectorAll('[data-time]'))b.onclick=()=>{stop();age=Number(b.dataset.time);draw();};
$('#play').onclick=()=>{if(age>=1280)age=960;playing=!playing;last=undefined;$('#play').textContent=playing?'暫停':'播放（¼ 倍）';draw();};
document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();draw();}});
function tick(now){if(playing){if(last!==undefined)age=Math.min(1280,age+Math.min(now-last,60)*.25);if(age>=1280)stop();draw();}last=now;requestAnimationFrame(tick);}
try{
 const start=performance.now();while(!frames.every(f=>f.contentWindow.freeArmSettle?.ready)){if(performance.now()-start>15000)throw Error('兩個版本未能完成載入，請重新整理。');await new Promise(r=>setTimeout(r,50));}
 ready=true;$('#controls').disabled=false;draw();requestAnimationFrame(tick);
}catch(e){$('#status').textContent=e.message;throw e;}
