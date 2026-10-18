/** Render genuine 1080p/30fps frames with Babylon, then encode a downloadable H.264 MP4. */
import fs from 'node:fs/promises';
import http from 'node:http';
import {spawn,execFileSync} from 'node:child_process';
import {once} from 'node:events';
import {build} from 'esbuild';
import {chromium} from '@playwright/test';
import {createHash} from 'node:crypto';
const root='docs/experiments/future-sanada',out=`${root}/comparison`;
await fs.mkdir(out,{recursive:true});
const result=await build({entryPoints:['tools/trellis_comparison_scene.ts'],bundle:true,format:'iife',minify:true,write:false,target:'es2022'});
const html=`<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><link rel="icon" href="data:,"><style>
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#090d12;color:#e9dfce;font-family:'Noto Sans CJK TC',sans-serif}header{height:132px;display:flex;align-items:center;padding:0 48px;border-bottom:1px solid #716044}h1{font-size:28px;letter-spacing:5px;margin:0 24px 0 0}header p{font-size:18px;color:#a9b1b9;margin:0}main{display:flex;height:848px}section{position:relative;width:960px}section+section{border-left:1px solid #716044}canvas{display:block;width:960px;height:848px}.label{position:absolute;top:16px;left:24px;display:flex;align-items:center;gap:20px;background:#0b1017dc;padding:10px 12px;border-radius:3px}.badge{font-size:28px;color:#dcb97c;border:1px solid #8f7347;padding:6px 14px}.model{font-size:24px;font-weight:600}.sub{font-size:16px;color:#aab3bf;margin-top:4px}footer{height:100px;padding:19px 48px;display:flex;align-items:center;justify-content:space-between;border-top:1px solid #716044}#chapter{font-size:25px;letter-spacing:2px}.note{font-size:16px;color:#aab3bf;margin-top:5px}#time{font-size:20px;color:#dcb97c;font-variant-numeric:tabular-nums}#progress{position:absolute;bottom:0;height:4px;background:#a52e2b}
</style><header><h1>未來赤備 / 真田幸村</h1><p>同一張參考圖 · 同步鏡位與燈光 · 實際 3D 模型比較</p></header><main><section><canvas></canvas><div class="label"><div class="badge">DINOv2</div><div><div class="model">TRELLIS 第一代</div><div class="sub">149,998 面 · 2K 色彩貼圖</div></div></div></section><section><canvas></canvas><div class="label"><div class="badge">DINOv3</div><div><div class="model">TRELLIS.2</div><div class="sub">148,107 面 · 2K PBR 材質</div></div></div></section></main><footer><div><div id="chapter"></div><div class="note">第一代展示 metallic = 0；第二代沿用生成 PBR。兩套完整模型流程比較，非單一編碼器測試。</div></div><div id="time"></div></footer><div id="progress"></div><script>${result.outputFiles[0].text.replace(/<\/script/gi,'<\\/script')}</script></html>`;
const server=http.createServer(async(req,res)=>{
 try{if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end(html);return}
 if(!['/trellis1/future-sanada.glb','/future-sanada.glb'].includes(req.url)){res.writeHead(404).end();return}
 res.setHeader('Content-Type','model/gltf-binary');res.end(await fs.readFile(root+req.url));
 }catch{res.writeHead(500).end()}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const errors=[],external=[],started=Date.now();
let encoder;
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith('http://127.0.0.1:'))external.push(r.url())});
 await page.goto(`http://127.0.0.1:${server.address().port}`);
 await page.waitForFunction(()=>window.comparisonReady||window.comparisonError,null,{timeout:120000});
 const error=await page.evaluate(()=>window.comparisonError);if(error)throw new Error(error);
 await page.evaluate(()=>document.fonts.ready);
 const samples=[0,90,180,270,360,450,600,750,870];
 for(const frame of samples){await page.evaluate(f=>window.setFrame(f),frame);await page.screenshot({path:`${out}/frame-${String(frame).padStart(3,'0')}.png`})}
 console.log('Preview frames complete',Math.round((Date.now()-started)/1000),'seconds');
 if(process.argv.includes('--preview'))process.exitCode=0;
 else{
  const movie=`${out}/sanada-dinov2-vs-dinov3-1080p.mp4`;
  encoder=spawn('ffmpeg',['-y','-hide_banner','-loglevel','warning','-f','image2pipe','-framerate','30','-vcodec','png','-i','pipe:0','-an','-c:v','libx264','-preset','slow','-crf','21','-maxrate','6M','-bufsize','12M','-pix_fmt','yuv420p','-profile:v','high','-level:v','4.1','-movflags','+faststart','-threads','4',movie],{stdio:['pipe','ignore','inherit']});
  const done=once(encoder,'exit');
  encoder.stdin.on('error',()=>{});
  for(let frame=0;frame<900;frame++){
   await page.evaluate(f=>window.setFrame(f),frame);
   const png=await page.screenshot({type:'png'});
   if(encoder.exitCode!==null)throw new Error(`ffmpeg exited ${encoder.exitCode}`);
   if(!encoder.stdin.write(png))await once(encoder.stdin,'drain');
   if(frame%90===0)console.log(JSON.stringify({frame,total:900,elapsedSeconds:Math.round((Date.now()-started)/1000)}));
  }
  encoder.stdin.end();const [code]=await done;if(code!==0)throw new Error(`ffmpeg exited ${code}`);
  if(errors.length||external.length)throw new Error(JSON.stringify({errors,external}));
  const probe=JSON.parse(execFileSync('ffprobe',['-v','error','-count_frames','-show_streams','-show_format','-of','json',movie],{encoding:'utf8'}));
  const stream=probe.streams[0];if(stream.width!==1920||stream.height!==1080||stream.nb_read_frames!=='900'||stream.avg_frame_rate!=='30/1')throw new Error('Incorrect video format');
  const bytes=await fs.readFile(movie);
  const models=await Promise.all(['trellis1/future-sanada.glb','future-sanada.glb'].map(async name=>({name,sha256:createHash('sha256').update(await fs.readFile(`${root}/${name}`)).digest('hex')})));
  await fs.writeFile(`${out}/video-report.json`,JSON.stringify({renderer:'Babylon.js / Chromium SwiftShader, actual GLB geometry',width:1920,height:1080,fps:30,frames:900,durationSeconds:30,elapsedSeconds:(Date.now()-started)/1000,codec:stream.codec_name,pixelFormat:stream.pix_fmt,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),encoding:'libx264 slow CRF21, maxrate6M, yuv420p, faststart',models,errors,externalRequests:external,chapters:[{start:0,end:12,title:'360 turntable'},{start:12,end:17,title:'helmet and mask'},{start:17,end:22,title:'armor and materials'},{start:22,end:27,title:'wrist and fingers'},{start:27,end:30,title:'full comparison'}],limitations:['No rig or character animation; synchronized camera motion only','Same normalized height, lighting and camera; first-generation display metallic=0','Different complete pipelines, not an encoder-only benchmark','CPU software WebGL offline render, not a mobile performance benchmark']},null,2)+'\n');
  console.log(JSON.stringify({movie,bytes:bytes.length,frames:stream.nb_read_frames}));
 }
}finally{if(encoder&&encoder.exitCode===null)encoder.kill();await browser.close();await new Promise(r=>server.close(r))}
