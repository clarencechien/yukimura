const $=s=>document.querySelector(s),frames=[...document.querySelectorAll('iframe')],views=[$('#before'),$('#after')];
let age=1180,playing=false,last,ready=false;
function stop(){playing=false;$('#play').textContent='播放（¼ 倍）';}
function draw(){
 if(!ready)return;
 const states=frames.map((frame,i)=>{const doc=frame.contentDocument,input=doc.querySelector('#time');input.value=age;input.dispatchEvent(new frame.contentWindow.Event('input'));const source=doc.querySelector('#view');views[i].getContext('2d').drawImage(source,600,330,600,260,0,0,600,260);return frame.contentWindow.freeArmSettle;});
 $('#age').textContent=`${age.toFixed(1)} ms`;$('#time').value=age;$('#status').textContent=age<=1200?'過渡前：共用原卸力姿勢。':age<=1240?'右側顯示低頭過渡格；兩側時間相同。':age<1260?'已接回原側倒圖，肩部完成短暫銜接。':'1260 ms 後：兩版本的動作相同。';
 window.bridgeReview={ready:true,age,playing,sourceAges:states.map(s=>s.age),frameIds:states.map(s=>s.fall.frames[s.pose.fallFrame]?.id??'unload')};
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
