import {Engine} from '@babylonjs/core/Engines/engine';
import {Scene} from '@babylonjs/core/scene';
import {ArcRotateCamera} from '@babylonjs/core/Cameras/arcRotateCamera';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {Color3,Color4} from '@babylonjs/core/Maths/math.color';
import {HemisphericLight} from '@babylonjs/core/Lights/hemisphericLight';
import {DirectionalLight} from '@babylonjs/core/Lights/directionalLight';
import {SceneLoader} from '@babylonjs/core/Loading/sceneLoader';
import '@babylonjs/loaders/glTF/glTFFileLoader';
import '@babylonjs/loaders/glTF/2.0/glTFLoader';
import {winterReflections} from '../src/lighting';
const canvas=document.querySelector('canvas')!;
const engine=new Engine(canvas,true,{preserveDrawingBuffer:true,stencil:true});
engine.setHardwareScalingLevel(Math.max(1,devicePixelRatio/1.5));
const scene=new Scene(engine);scene.clearColor=new Color4(.075,.085,.09,1);
const camera=new ArcRotateCamera('hand camera',1.0,1.0,.38,new Vector3(0,0,0),scene);
camera.upVector=new Vector3(0,-1,0);
camera.minZ=.001;camera.lowerRadiusLimit=.18;camera.upperRadiusLimit=1.1;camera.wheelPrecision=250;
camera.panningSensibility=3000;camera.attachControl(canvas,true);
const sky=new HemisphericLight('sky',new Vector3(0,1,0),scene);sky.intensity=.8;sky.groundColor=new Color3(.3,.32,.36);
const key=new DirectionalLight('key',new Vector3(-.6,-1,-.4),scene);key.intensity=2.5;key.diffuse=new Color3(1,.86,.7);
winterReflections(scene);
const data=(window as any).embeddedHands;
let current:any=null;let loading=false;let lod=0;let rotate=false;
async function load(level:number){
 if(loading)return;loading=true;document.querySelector('#status')!.textContent='載入模型…';
 try{
  const bytes=Uint8Array.from(atob(data[level]),c=>c.charCodeAt(0));const url=URL.createObjectURL(new Blob([bytes],{type:'model/gltf-binary'}));
  let loaded;try{loaded=await SceneLoader.LoadAssetContainerAsync('',url,scene,undefined,'.glb');}finally{URL.revokeObjectURL(url)}
  if(current){current.removeAllFromScene();current.dispose()}current=loaded;current.addAllToScene();lod=level;
  const meshes=current.meshes.filter((m:any)=>m.getTotalVertices()>0);
  current.meshes.forEach((m:any)=>m.computeWorldMatrix(true));
  const bounds=meshes[0].getHierarchyBoundingVectors(true);camera.target=Vector3.Center(bounds.min,bounds.max);
  camera.radius=.48*Math.max(1,1/engine.getAspectRatio(camera));
  await scene.whenReadyAsync();scene.render();
  const fallback=document.querySelector<HTMLElement>("#fallback");if(fallback)fallback.hidden=true;
  const tri=meshes.reduce((n:number,m:any)=>n+m.getTotalIndices()/3,0);
  document.querySelector('#status')!.textContent=`LOD ${level} · ${tri.toLocaleString()} 三角面 · ${(bytes.length/1048576).toFixed(2)} MiB · 1 材質 · 22 骨骼`;
  (window as any).handPreview={ready:true,scene,camera,loaded:current,load,lod};
 }catch(e){document.querySelector('#status')!.textContent='載入失敗：'+String(e);throw e}finally{loading=false}
}
document.querySelectorAll<HTMLButtonElement>('[data-lod]').forEach(b=>b.onclick=()=>load(Number(b.dataset.lod)));
document.querySelector('#palm')!.addEventListener('click',()=>camera.alpha+=Math.PI);
document.querySelector('#rotate')!.addEventListener('click',()=>{rotate=!rotate;document.querySelector('#rotate')!.textContent=rotate?'停止旋轉':'自動旋轉'});
engine.runRenderLoop(()=>{if(rotate)camera.alpha+=engine.getDeltaTime()*.0003;key.direction=camera.target.subtract(camera.position).normalize();scene.render()});
window.addEventListener('resize',()=>engine.resize());load(matchMedia('(max-width:600px)').matches?1:0);
