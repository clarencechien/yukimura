/** Deterministic two-model review. Each frame renders both actual GLBs at the same camera pose. */
import {Engine,Scene,ArcRotateCamera,Vector3,Color3,Color4,HemisphericLight,DirectionalLight,SceneLoader,PBRMaterial,TransformNode,Camera,MeshBuilder,ShadowGenerator} from '@babylonjs/core';
import '@babylonjs/loaders/glTF';
import {winterReflections} from '../src/lighting';

const views: {scene: Scene; camera: ArcRotateCamera; engine: Engine}[]=[];
const smooth=(v:number)=>{v=Math.max(0,Math.min(1,v));return v*v*(3-2*v)};
type Shot={angle:number;span:number;target:number[];label:string};
const full:Shot={angle:90,span:2.32,target:[0,1.02,0],label:'01 / 360° 全身旋轉'};
function blend(a:Shot,b:Shot,t:number):Shot{const s=smooth(t);return {...b,angle:a.angle+(b.angle-a.angle)*s,span:a.span+(b.span-a.span)*s,target:a.target.map((v,i)=>v+(b.target[i]-v)*s)}}
function shot(time:number):Shot{
 if(time<=12)return {...full,angle:90+360*time/12};
 const head:Shot={angle:90,span:.76,target:[0,1.72,0],label:'02 / 鹿角・六文錢・面頬'};
 const armor:Shot={angle:90,span:1.00,target:[0,1.20,0],label:'03 / 胸甲・肩甲・材質'};
 const hand:Shot={angle:90,span:.64,target:[-.40,.83,0],label:'04 / 護腕・手指・關節'};
 if(time<13)return blend(full,head,time-12);
 if(time<17)return {...head,angle:90+22*Math.sin((time-13)/4*Math.PI*2)};
 if(time<18)return blend(head,armor,time-17);
 if(time<22)return {...armor,angle:90+25*Math.sin((time-18)/4*Math.PI*2)};
 if(time<23)return blend(armor,hand,time-22);
 if(time<27)return {...hand,angle:90+18*Math.sin((time-23)/4*Math.PI*2)};
 const end={...full,angle:110,label:'05 / 同圖生成・實際 3D 網格'};
 if(time<28)return blend(hand,end,time-27);
 return end;
}
async function init(){
 for(const [index,path] of ['/trellis1/future-sanada.glb','/future-sanada.glb'].entries()){
  const canvas=document.querySelectorAll('canvas')[index];
  const engine=new Engine(canvas,true,{preserveDrawingBuffer:true,stencil:true});
  engine.setSize(960,848);
  const scene=new Scene(engine);scene.clearColor=new Color4(.035,.045,.060,1);
  winterReflections(scene);scene.environmentIntensity=.85;scene.imageProcessingConfiguration.exposure=1.45;
  const camera=new ArcRotateCamera('comparison camera',Math.PI/2,1.47,5,new Vector3(0,1,0),scene);
  camera.mode=Camera.ORTHOGRAPHIC_CAMERA;camera.minZ=.01;camera.maxZ=30;
  const fill=new HemisphericLight('ambient',new Vector3(0,1,0),scene);fill.intensity=.65;fill.groundColor=new Color3(.22,.20,.18);
  const key=new DirectionalLight('warm key',new Vector3(-1,-1,-1),scene);key.position=new Vector3(3,5,4);key.intensity=2.4;key.diffuse=new Color3(1,.91,.8);
  const cool=new DirectionalLight('cool fill',new Vector3(1,-.4,.5),scene);cool.intensity=1.35;cool.diffuse=new Color3(.75,.86,1);
  const rim=new DirectionalLight('edge',new Vector3(-.3,-1,1),scene);rim.intensity=1.1;rim.diffuse=new Color3(1,.93,.85);
  const imported=await SceneLoader.ImportMeshAsync('','',path,scene,undefined,'.glb');
  const root=imported.meshes[0];const bounds=root.getHierarchyBoundingVectors();
  const height=bounds.max.y-bounds.min.y,scale=2/height;
  const norm=new TransformNode('normalize 2m',scene);root.parent=norm;norm.scaling.setAll(scale);
  norm.position.set(-(bounds.max.x+bounds.min.x)*scale/2,-bounds.min.y*scale,-(bounds.max.z+bounds.min.z)*scale/2);
  const meshes=imported.meshes.filter(m=>m.getTotalVertices()>0);
  if(index===0)for(const mesh of meshes)if(mesh.material instanceof PBRMaterial)mesh.material.metallic=0;
  const ground=MeshBuilder.CreateGround('floor',{width:200,height:200},scene);ground.position.y=-.008;ground.receiveShadows=true;
  const material=new PBRMaterial('matte floor',scene);material.albedoColor=new Color3(.008,.010,.014);material.metallic=0;material.roughness=.9;ground.material=material;
  const shadow=new ShadowGenerator(1024,key);shadow.usePercentageCloserFiltering=true;shadow.bias=.001;shadow.normalBias=.015;shadow.setDarkness(.30);
  meshes.forEach(m=>shadow.addShadowCaster(m));
  views.push({scene,camera,engine});
  await scene.whenReadyAsync();
 }
 (window as any).setFrame=(frame:number)=>{
  const time=frame/30,state=shot(time),angle=state.angle*Math.PI/180;
  for(const {scene,camera,engine} of views){
   camera.alpha=angle;camera.beta=1.47;camera.target.set(...state.target as [number,number,number]);
   camera.orthoTop=state.span/2;camera.orthoBottom=-state.span/2;camera.orthoLeft=-state.span/2*960/848;camera.orthoRight=state.span/2*960/848;
   scene.render();(engine as any)._gl.finish();
  }
  document.querySelector('#chapter')!.textContent=state.label;
  document.querySelector('#time')!.textContent=`${time.toFixed(1).padStart(4,'0')} / 30.0s`;
  (document.querySelector('#progress') as HTMLElement).style.width=`${frame/899*100}%`;
  return state;
 };
 (window as any).setFrame(0);
 (window as any).comparisonReady=true;
}
init().catch(error=>{(window as any).comparisonError=String(error);console.error(error)});
