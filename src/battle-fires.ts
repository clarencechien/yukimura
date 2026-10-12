import {Scene} from '@babylonjs/core/scene';
import {ParticleSystem} from '@babylonjs/core/Particles/particleSystem';
import {DynamicTexture} from '@babylonjs/core/Materials/Textures/dynamicTexture';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {Color3,Color4} from '@babylonjs/core/Maths/math.color';
import {Mesh} from '@babylonjs/core/Meshes/mesh';
import {MeshBuilder} from '@babylonjs/core/Meshes/meshBuilder';
import {StandardMaterial} from '@babylonjs/core/Materials/standardMaterial';

/** Eight fires share two small native particle pools and one generated sprite. */
export function battleFires(scene:Scene,reduced:boolean){
 const mobile=matchMedia('(pointer:coarse)').matches;
 const texture=new DynamicTexture('wind torn fire pigment',{width:64,height:128},scene,false);
 const ctx=texture.getContext();ctx.clearRect(0,0,64,128);
 for(let i=0;i<7;i++){
  const x=32+Math.sin(i*1.6)*i*1.2,y=99-i*12,r=22-i*2.6,g=ctx.createRadialGradient(x,y,0,x,y,r);
  g.addColorStop(0,'rgba(255,255,255,.95)');g.addColorStop(.45,'rgba(255,255,255,.65)');g.addColorStop(1,'rgba(255,255,255,0)');ctx.fillStyle=g;ctx.fillRect(0,0,64,128);
 }texture.hasAlpha=true;texture.update();
 const origins=[6,43,88,138].flatMap(z=>[-8.6,8.6].map(x=>new Vector3(x,2.08,z)));
 // A small anchored flame bed keeps the fire connected to the fuel while
 // individual tongues rise away. Vertical cards never tilt through the bowl.
 const bedMaterial=new StandardMaterial('brazier flame bed pigment',scene);bedMaterial.diffuseTexture=texture;bedMaterial.useAlphaFromDiffuseTexture=true;bedMaterial.disableLighting=true;bedMaterial.emissiveColor=new Color3(1,.56,.16);bedMaterial.backFaceCulling=false;
 const beds=origins.map(o=>{const mesh=MeshBuilder.CreatePlane('anchored flame bed',{width:.65,height:1},scene);mesh.position.set(o.x,2.10,o.z);mesh.material=bedMaterial;mesh.billboardMode=Mesh.BILLBOARDMODE_Y;mesh.isPickable=false;return mesh;});
 const flame=new ParticleSystem('brazier flame tongues',reduced?48:mobile?96:160,scene);flame.particleTexture=texture;flame.emitter=Vector3.Zero();
 flame.startPositionFunction=(_matrix,p)=>{const o=origins[Math.floor(Math.random()*origins.length)];p.copyFrom(o).addInPlaceFromFloats((Math.random()-.5)*.34,Math.random()*.10,(Math.random()-.5)*.34);};
 flame.direction1=new Vector3(.12,1.1,.05);flame.direction2=new Vector3(.45,1.7,.12);flame.minEmitPower=1;flame.maxEmitPower=1;
 flame.minSize=.29;flame.maxSize=.55;flame.minScaleY=1.8;flame.maxScaleY=2.8;flame.minLifeTime=.35;flame.maxLifeTime=.65;flame.emitRate=reduced?65:140;
 flame.addColorGradient(0,new Color4(1,.78,.34,0));flame.addColorGradient(.12,new Color4(1,.83,.43,.82));flame.addColorGradient(.5,new Color4(1,.31,.055,.65));flame.addColorGradient(1,new Color4(.43,.09,.025,0));
 // Babylon size gradients specify metres, overriding minSize/maxSize. Keep
 // the lower edge above the bowl instead of glowing through its underside.
 flame.addSizeGradient(0,.22);flame.addSizeGradient(.3,.38);flame.addSizeGradient(1,.06);flame.blendMode=ParticleSystem.BLENDMODE_STANDARD;flame.start();
 const ember=new ParticleSystem('rising brazier embers',reduced?12:32,scene);ember.particleTexture=texture;ember.emitter=Vector3.Zero();ember.startPositionFunction=flame.startPositionFunction;
 ember.direction1=new Vector3(.4,1.2,.1);ember.direction2=new Vector3(1.2,2,.5);ember.minEmitPower=1;ember.maxEmitPower=1;ember.minLifeTime=1;ember.maxLifeTime=2;ember.minSize=.025;ember.maxSize=.07;
 ember.color1=new Color4(1,.57,.14,.8);ember.color2=new Color4(1,.24,.035,.6);ember.colorDead=new Color4(.2,.08,.01,0);ember.emitRate=reduced?4:16;ember.blendMode=ParticleSystem.BLENDMODE_ADD;ember.start();
 return {update(t:number){beds.forEach((mesh,i)=>{const height=.77+(reduced?0:Math.sin(t*7+i)*.07);mesh.scaling.y=height;mesh.position.y=1.72+height*.5;});},pause(paused:boolean){flame.updateSpeed=paused?0:.01;ember.updateSpeed=paused?0:.01;},get active(){return flame.getActiveCount()+ember.getActiveCount();},capacity:flame.getCapacity()+ember.getCapacity()};
}
