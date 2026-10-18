/** Validate the compressed movie, not only the pre-encode screenshots. */
import fs from 'node:fs/promises';
import http from 'node:http';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {chromium} from '@playwright/test';
const folder='docs/experiments/future-sanada/comparison',movie=`${folder}/sanada-dinov2-vs-dinov3-1080p.mp4`;
await fs.mkdir('.tmp/trellis-comparison',{recursive:true});
const data=await fs.readFile(movie),atoms=[];
for(let offset=0;offset<data.length;){let size=data.readUInt32BE(offset);const type=data.toString('ascii',offset+4,offset+8);if(size===1)size=Number(data.readBigUInt64BE(offset+8));if(size===0)size=data.length-offset;assert(size>=8);atoms.push({type,offset,size});offset+=size}
assert(atoms.find(a=>a.type==='moov').offset<atoms.find(a=>a.type==='mdat').offset,'faststart metadata must precede movie data');
const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',movie],{encoding:'utf8'}));
assert.equal(probe.streams.length,1);const stream=probe.streams[0];assert.equal(stream.codec_name,'h264');assert.equal(stream.pix_fmt,'yuv420p');assert.equal(stream.nb_read_frames,'900');assert.equal(stream.avg_frame_rate,'30/1');assert.equal(Number(probe.format.duration),30);
execFileSync('ffmpeg',['-v','error','-xerror','-i',movie,'-f','null','-'],{stdio:'pipe'});
const quality=[];
for(const frame of [0,450,600,750]){
 const stats=`.tmp/trellis-comparison/ssim-${frame}.txt`;
 execFileSync('ffmpeg',['-v','error','-i',`${folder}/frame-${String(frame).padStart(3,'0')}.png`,'-ss',String(frame/30),'-i',movie,'-filter_complex',`[0:v]format=yuv420p[a];[1:v]format=yuv420p[b];[a][b]ssim=stats_file=${stats}`,'-frames:v','1','-f','null','-']);
 const text=await fs.readFile(stats,'utf8');const score=Number(text.match(/All:([\d.]+)/)[1]);assert(score>.95,`Frame ${frame} SSIM ${score}`);quality.push({frame,ssim:score});
}
const server=http.createServer((req,res)=>{
 if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end('<!doctype html><meta charset="utf-8"><link rel="icon" href="data:,"><style>body{margin:0;background:black}video{display:block;width:100vw;height:100vh;object-fit:contain}</style><video muted playsinline preload="auto" src="/movie.mp4"></video>');return}
 if(req.url!=='/movie.mp4'){res.writeHead(404).end();return}
 res.setHeader('Content-Type','video/mp4');res.setHeader('Accept-Ranges','bytes');
 const range=req.headers.range?.match(/bytes=(\d+)-(\d*)/);
 if(range){const start=Number(range[1]),end=range[2]?Number(range[2]):data.length-1;res.writeHead(206,{'Content-Range':`bytes ${start}-${end}/${data.length}`,'Content-Length':end-start+1});res.end(data.subarray(start,end+1))}
 else{res.setHeader('Content-Length',data.length);res.end(data)}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
const errors=[],checks=[];
try{
 for(const viewport of [{width:1920,height:1080},{width:390,height:844}]){
  const page=await browser.newPage({viewport});page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  await page.waitForFunction(()=>document.querySelector('video').readyState>=2);
  const state=await page.evaluate(async()=>{const v=document.querySelector('video');await v.play();return {width:v.videoWidth,height:v.videoHeight,duration:v.duration,codec:v.canPlayType('video/mp4; codecs="avc1.640029"')}});
  assert.equal(state.width,1920);assert.equal(state.height,1080);assert.equal(state.duration,30);
  await page.waitForFunction(()=>document.querySelector('video').currentTime>.2);
  await page.evaluate(()=>document.querySelector('video').pause());
  for(const time of [3,6,9,15,20,25,29]){
   await page.evaluate(t=>new Promise((resolve,reject)=>{const v=document.querySelector('video');v.addEventListener('seeked',resolve,{once:true});v.addEventListener('error',reject,{once:true});v.currentTime=t}),time);
   assert.equal(await page.evaluate(()=>document.querySelector('video').error),null);
   if(time===15&&viewport.width===1920)await page.screenshot({path:`${folder}/encoded-detail.png`});
  }
  checks.push({viewport,state,playback:'advanced successfully',seekSeconds:[3,6,9,15,20,25,29],horizontalOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)});
  await page.close();
 }
 assert.deepEqual(errors,[]);
 await fs.writeFile(`${folder}/video-verification.json`,JSON.stringify({passed:true,fullDecode:'900 frames, ffmpeg -xerror',faststart:true,bytes:data.length,sampleCompressionSSIM:quality,browserChecks:checks,pageErrors:errors,limitation:'Chromium desktop and mobile viewport; not a physical iPhone/Android device test'},null,2)+'\n');
 console.log(JSON.stringify({passed:true,bytes:data.length,quality,checks}));
}finally{await browser.close();await new Promise(r=>server.close(r))}
