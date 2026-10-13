import {Engine,Scene,ArcRotateCamera,Vector3,Color3,Color4,HemisphericLight,DirectionalLight,SceneLoader} from '@babylonjs/core';
import '@babylonjs/loaders/glTF';
import {winterReflections} from '../src/lighting';

const engine=new Engine(document.querySelector('canvas')!,true,{preserveDrawingBuffer:true});
const scene=new Scene(engine);scene.clearColor=new Color4(.075,.1,.12,1);
const camera=new ArcRotateCamera('camera',Math.PI/2-.18,1.4,3.1,new Vector3(0,1,0),scene);
camera.minZ=.01;camera.attachControl();
const sky=new HemisphericLight('sky',new Vector3(0,1,0),scene);sky.intensity=.6;
const sun=new DirectionalLight('sun',new Vector3(-.3,-1,-1),scene);sun.intensity=1.7;sun.diffuse=new Color3(1,.85,.72);
winterReflections(scene);
const kind=new URLSearchParams(location.search).get('model')==='cyber-samurai'?'cyber-samurai':'rocketbox';
const loaded=await SceneLoader.ImportMeshAsync('','/review/candidates/',`${kind}.glb`,scene);
await scene.whenReadyAsync();
scene.render();
Object.assign(window,{candidatePreview:{scene,camera,loaded,ready:true}});
engine.runRenderLoop(()=>scene.render());
window.addEventListener('resize',()=>engine.resize());
