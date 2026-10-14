/** Bake glTF skin palettes for Babylon's native BakedVertexAnimationManager.
 * Uses Babylon matrix/quaternion math; the browser does no animation baking.
 */
import {readFileSync,writeFileSync,readdirSync,unlinkSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {Matrix,Quaternion,Vector3} from '@babylonjs/core/Maths/math.vector.js';
const root=new URL('../public/models/',import.meta.url),fps=60,report={fps,models:{}};
const used=new Set();
for(const name of ['ashigaru','tokugawa','ieyasu']){
 const bytes=readFileSync(new URL(name+'.glb',root));const len=bytes.readUInt32LE(12),g=JSON.parse(bytes.toString('utf8',20,20+len)),bin=bytes.subarray(28+len);
 const read=index=>{const a=g.accessors[index],v=g.bufferViews[a.bufferView],offset=(v.byteOffset||0)+(a.byteOffset||0),size={SCALAR:1,VEC3:3,VEC4:4,MAT4:16}[a.type];if(a.componentType!==5126)throw Error('Expected float animation data');return Array.from({length:a.count},(_,i)=>Array.from({length:size},(_,j)=>bin.readFloatLE(offset+i*(v.byteStride||size*4)+j*4)));};
 const skin=g.skins[0],inverse=read(skin.inverseBindMatrices).map(a=>Matrix.FromArray(a)),parents=g.nodes.map(()=>-1);
 g.nodes.forEach((n,i)=>(n.children||[]).forEach(c=>parents[c]=i));
 const meshNode=g.nodes.findIndex(n=>n.skin===0),frames=[],clips={};
 function palette(channels,time){
  const nodes=g.nodes.map(n=>({t:Vector3.FromArray(n.translation||[0,0,0]),r:Quaternion.FromArray(n.rotation||[0,0,0,1]),s:Vector3.FromArray(n.scale||[1,1,1])}));
  for(const {node,path,times,values,interpolation} of channels){
   let i=0;while(i<times.length-2&&times[i+1][0]<time)i++;
   const j=Math.min(i+1,times.length-1),a=Math.max(0,Math.min(1,(time-times[i][0])/(times[j][0]-times[i][0]||1)));
   const blend=interpolation==='STEP'?(time>=times[j][0]?1:0):a;
   const n=nodes[node];if(path==='rotation')n.r=Quaternion.Slerp(Quaternion.FromArray(values[i]),Quaternion.FromArray(values[j]),blend);
   else n[path==='translation'?'t':'s']=Vector3.Lerp(Vector3.FromArray(values[i]),Vector3.FromArray(values[j]),blend);
  }
  const global=[];
  function world(i){if(global[i])return global[i];const n=nodes[i],local=g.nodes[i].matrix?Matrix.FromArray(g.nodes[i].matrix):Matrix.Compose(n.s,n.r,n.t);return global[i]=parents[i]<0?local:local.multiply(world(parents[i]));}
  const invMesh=Matrix.Invert(world(meshNode));
  const output=skin.joints.flatMap((j,i)=>Array.from(inverse[i].multiply(world(j)).multiply(invMesh).m));
  output.push(...Matrix.Identity().m);return output;
 }
 for(const clip of g.animations){
  const channels=clip.channels.map(c=>{const s=clip.samplers[c.sampler];if(s.interpolation&&!['LINEAR','STEP'].includes(s.interpolation))throw Error('Unsupported interpolation');return {interpolation:s.interpolation,node:c.target.node,path:c.target.path,times:read(s.input),values:read(s.output)};});
  const duration=Math.max(...channels.map(c=>c.times.at(-1)[0]));const start=frames.length,count=Math.round(duration*fps)+1;
  for(let i=0;i<count;i++)frames.push(palette(channels,Math.min(duration,i/fps)));
  clips[clip.name]={start,end:frames.length-1,duration};
 }
 const data=new Float32Array(frames.flat());if(!data.every(Number.isFinite))throw Error('Non-finite bone palette');
 const raw=Buffer.from(data.buffer),uri='shared/'+createHash('sha256').update(raw).digest('hex').slice(0,16)+'.bin';writeFileSync(new URL(uri,root),raw);used.add(uri.slice(7));
 report.models[name]={source_sha256:createHash('sha256').update(bytes).digest('hex'),uri,bytes:raw.length,width:(skin.joints.length+1)*4,height:frames.length,joints:skin.joints.length,clips};
}
for(const file of readdirSync(new URL('shared/',root)))if(/^[a-f0-9]{16}\.bin$/.test(file)&&!used.has(file))unlinkSync(new URL('shared/'+file,root));
writeFileSync(new URL('crowd-animation.json',root),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({models:Object.keys(report.models),uniquePalettes:used.size,bytes:[...used].reduce((sum,f)=>sum+readFileSync(new URL('shared/'+f,root)).length,0)}));
