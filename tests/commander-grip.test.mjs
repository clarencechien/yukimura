import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {Matrix,Quaternion,Vector3} from '@babylonjs/core/Maths/math.vector.js';
const source=JSON.parse(readFileSync(new URL('../assets/vendor/mpfb/commander-grip.json',import.meta.url)));
const modelsRoot=new URL(process.env.MODEL_TEST_ROOT||'../public/models/',import.meta.url);
const configPath=process.env.GRIP_POSE_CONFIG||new URL('weapon-grips.json',modelsRoot);
const poseConfig=existsSync(configPath)?JSON.parse(readFileSync(configPath)):null;
const gltfPoint=p=>new Vector3(p[0],p[2],-p[1]);
for(const kind of ['yukimura','ieyasu'])test(`${kind}: exported hands stay aligned to their weapon throughout combat clips`,()=>{
 const bytes=readFileSync(new URL(`${kind}.glb`,modelsRoot)),n=bytes.readUInt32LE(12),g=JSON.parse(bytes.toString('utf8',20,20+n)),bin=bytes.subarray(28+n);
 const read=i=>{const a=g.accessors[i],v=g.bufferViews[a.bufferView],size={SCALAR:1,VEC3:3,VEC4:4,MAT4:16}[a.type];assert.equal(a.componentType,5126);return Array.from({length:a.count},(_,r)=>Array.from({length:size},(_,c)=>bin.readFloatLE((v.byteOffset||0)+(a.byteOffset||0)+r*(v.byteStride||size*4)+c*4)))};
 const skin=g.skins[0],inverse=read(skin.inverseBindMatrices).map(x=>Matrix.FromArray(x)),parents=g.nodes.map(()=>-1);
 g.nodes.forEach((node,i)=>(node.children||[]).forEach(j=>parents[j]=i));
 const joint=name=>skin.joints.findIndex(i=>g.nodes[i].name===name),weapon=joint('weapon');
 if(kind==='ieyasu'){
  const p=g.meshes[0].primitives[0],positions=read(p.attributes.POSITION),weights=read(p.attributes.WEIGHTS_0);
  const a=g.accessors[p.attributes.JOINTS_0],view=g.bufferViews[a.bufferView],step=a.componentType===5121?1:2;
  assert.ok([5121,5123].includes(a.componentType));
  const origin=gltfPoint([.47*.82,-.16*.9-(.91*1.25-1.05)*.1,.91*1.25]);
  const axis=gltfPoint([0,-Math.sin(.28),Math.cos(.28)]),axial=[];
  for(let i=0;i<positions.length;i++){
   const ids=Array.from({length:4},(_,c)=>{const offset=(view.byteOffset||0)+(a.byteOffset||0)+i*(view.byteStride||step*4)+c*step;return step===1?bin.readUInt8(offset):bin.readUInt16LE(offset)});
   if(!ids.some((j,c)=>j===weapon&&weights[i][c]>.99))continue;
   const delta=Vector3.FromArray(positions[i]).subtract(origin),t=Vector3.Dot(delta,axis);
   if(t>=-.232&&t<=.155&&delta.subtract(axis.scale(t)).length()<.020)axial.push(t);
  }
  assert.ok(axial.length>=12&&Math.min(...axial)<-.225&&Math.max(...axial)>.15,'tachi hilt must extend beneath the lower hand');
 }
 let samples=0,maxError=0,minDot=1,maxWristAngle=0,worstPose=null;const clipMetrics={};
 for(const clip of g.animations.filter(c=>!c.name.startsWith('fall'))){
  const measured=clipMetrics[clip.name]={maxWristAngle:0,maxGripErrorM:0,minAxisDot:1};
  const channels=clip.channels.map(c=>{const s=clip.samplers[c.sampler];return {node:c.target.node,path:c.target.path,times:read(s.input).flat(),values:read(s.output)}});
  const duration=Math.max(...channels.map(c=>c.times.at(-1)));
  const expected={idle:1.6,run:.8,slash:1,reverse:1,thrust:1,spin:1.2,dash:.6,hurt:.6}[clip.name];
  assert.ok(Math.abs(duration-expected)<1e-5,'animation sampling changed gameplay duration');
  for(const channel of channels.filter(c=>c.path==='rotation'&&(g.nodes[c.node].name.includes('arm.')||g.nodes[c.node].name.startsWith('body.lowerarm')))){
   const first=channel.values[0],last=channel.values.at(-1),dot=Math.abs(first.reduce((sum,x,i)=>sum+x*last[i],0));
   assert.ok(dot>.9999,`${clip.name}: arm does not return to its starting orientation`);
  }
  for(let f=0;f<=97;f++){
   const t=duration*f/97,nodes=g.nodes.map(n=>({p:Vector3.FromArray(n.translation||[0,0,0]),q:Quaternion.FromArray(n.rotation||[0,0,0,1]),s:Vector3.FromArray(n.scale||[1,1,1])}));
   for(const c of channels){let a=0;while(a<c.times.length-2&&c.times[a+1]<t)a++;const b=Math.min(a+1,c.times.length-1),mix=Math.max(0,Math.min(1,(t-c.times[a])/(c.times[b]-c.times[a]||1)));const node=nodes[c.node];if(c.path==='rotation')node.q=Quaternion.Slerp(Quaternion.FromArray(c.values[a]),Quaternion.FromArray(c.values[b]),mix);else node[c.path==='translation'?'p':'s']=Vector3.Lerp(Vector3.FromArray(c.values[a]),Vector3.FromArray(c.values[b]),mix)}
   const worlds=[];function world(i){if(worlds[i])return worlds[i];const n=nodes[i],local=g.nodes[i].matrix?Matrix.FromArray(g.nodes[i].matrix):Matrix.Compose(n.s,n.q,n.p);return worlds[i]=parents[i]<0?local:local.multiply(world(parents[i]))}
   const delta=j=>inverse[j].multiply(world(skin.joints[j])),wd=delta(weapon);
   const origin=Vector3.TransformCoordinates(gltfPoint([.47*.82,-.16*.9-(.91*1.25-1.05)*.1,.91*1.25]),wd);
   const axis=Vector3.TransformNormal(gltfPoint([0,-Math.sin(.28),Math.cos(.28)]),wd).normalize();
   for(const [side,sign] of [['R',1],['L',-1]]){
    const scale=.022*.9/source.shaft_radius,c=source.shaft_center;
    const center=gltfPoint([sign*.47*.82-sign*c[0]*scale,-.16*.9-(.94*1.25-1.05)*.1-c[2]*scale,.94*1.25-c[1]*scale]);
    const deformWrist=joint('body.wrist.'+side);
    const hd=delta(deformWrist>=0?deformWrist:joint('hand.'+side)),actual=Vector3.TransformCoordinates(center,hd);
    const authoredSpacing=poseConfig?.[kind]?.clips?.[clip.name]?.spacing;
    const spacing=side==='R'?0:authoredSpacing??(kind==='ieyasu'?-.15:['thrust','dash'].includes(clip.name)?.30:.42);
    const elbow=Vector3.TransformCoordinates(Vector3.Zero(),world(skin.joints[joint('forearm.'+side)]));
    const wrist=Vector3.TransformCoordinates(Vector3.Zero(),world(skin.joints[joint('hand.'+side)]));
    const palm=Vector3.TransformNormal(gltfPoint([0,0,-1]),hd).normalize();
    const bend=Math.acos(Math.max(-1,Math.min(1,Vector3.Dot(wrist.subtract(elbow).normalize(),palm))))*180/Math.PI;
    measured.maxWristAngle=Math.max(measured.maxWristAngle,bend);
    if(bend>maxWristAngle){maxWristAngle=bend;worstPose={clip:clip.name,side,t};}
    const error=Vector3.Distance(actual,origin.add(axis.scale(spacing)));maxError=Math.max(maxError,error);
    const a=source.shaft_axis,gripAxis=Vector3.TransformNormal(gltfPoint([-sign*a[0],-a[2],-a[1]]),hd).normalize();
    const dot=Vector3.Dot(gripAxis,axis);minDot=Math.min(minDot,dot);samples++;measured.maxGripErrorM=Math.max(measured.maxGripErrorM,error);measured.minAxisDot=Math.min(measured.minAxisDot,dot);
    assert.ok(error<.004,`${clip.name} ${side} t=${t}: grip error ${error} m`);
    assert.ok(dot>.999,`${clip.name} ${side}: grip axis not aligned`);
   }
  }
 }
 assert.ok(maxWristAngle<Number(process.env.GRIP_MAX_WRIST_ANGLE||50),`${kind}: wrist bends back excessively (${maxWristAngle} degrees)`);
 if(process.env.GRIP_REPORT_DIR){mkdirSync(process.env.GRIP_REPORT_DIR,{recursive:true});writeFileSync(join(process.env.GRIP_REPORT_DIR,kind+'.json'),JSON.stringify({kind,samples,maxGripErrorM:maxError,minAxisDot:minDot,maxWristAngle,worstPose,clips:clipMetrics},null,2)+'\n')}
 console.log(kind,{samples,maxGripErrorM:maxError,minAxisDot:minDot,maxWristAngle,worstPose});
});
