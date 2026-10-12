import {Scene} from '@babylonjs/core/scene';
import {ParticleSystem} from '@babylonjs/core/Particles/particleSystem';
import {DynamicTexture} from '@babylonjs/core/Materials/Textures/dynamicTexture';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {Color3,Color4} from '@babylonjs/core/Maths/math.color';
import {DirectionalLight} from '@babylonjs/core/Lights/directionalLight';

/** Native Babylon particles, bounded pools and one shared soft sprite. */
export function winterWeather(scene:Scene,sun:DirectionalLight,reduced:boolean){
 const mobile=matchMedia('(pointer:coarse)').matches;
 const texture=new DynamicTexture('soft winter particles',64,scene,false);
 const ctx=texture.getContext(),g=ctx.createRadialGradient(32,32,1,32,32,30);
 g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(.25,'rgba(255,255,255,.8)');g.addColorStop(1,'rgba(255,255,255,0)');ctx.fillStyle=g;ctx.fillRect(0,0,64,64);texture.hasAlpha=true;texture.update();
 const snow=new ParticleSystem('windborne snowfall',reduced?120:mobile?300:700,scene);
 snow.particleTexture=texture;snow.emitter=new Vector3(0,11,8);snow.minEmitBox=new Vector3(-23,-5,-22);snow.maxEmitBox=new Vector3(23,7,25);
 snow.color1=new Color4(.81,.88,.96,.60);snow.color2=new Color4(.58,.71,.83,.35);snow.colorDead=new Color4(.61,.74,.86,0);
 snow.minSize=.035;snow.maxSize=.12;snow.minLifeTime=4;snow.maxLifeTime=7;snow.emitRate=reduced?20:mobile?55:125;
 snow.minEmitPower=1;snow.maxEmitPower=1.8;snow.gravity=new Vector3(.12,-.18,0);snow.blendMode=ParticleSystem.BLENDMODE_STANDARD;snow.start();
 const drift=new ParticleSystem('ground spindrift',reduced?6:24,scene);drift.particleTexture=texture;
 drift.emitter=new Vector3(0,.18,8);drift.minEmitBox=new Vector3(-22,0,-14);drift.maxEmitBox=new Vector3(22,.15,30);
 drift.color1=new Color4(.56,.66,.73,.11);drift.color2=new Color4(.67,.75,.80,.06);drift.colorDead=new Color4(.6,.7,.76,0);
 drift.minScaleX=3;drift.maxScaleX=6;drift.minScaleY=.14;drift.maxScaleY=.4;drift.minSize=1;drift.maxSize=2;
 drift.minLifeTime=3;drift.maxLifeTime=5;drift.emitRate=reduced?1:5;drift.minEmitPower=1;drift.maxEmitPower=1;drift.blendMode=ParticleSystem.BLENDMODE_STANDARD;drift.start();
 let clock=0;
 return {pause(paused:boolean){snow.updateSpeed=paused?0:.01;drift.updateSpeed=paused?0:.01;},update(dt:number,target:Vector3){
  clock+=dt;const gust=.5+.5*Math.sin(clock*.31)+.22*Math.sin(clock*.93);
  (snow.emitter as Vector3).copyFrom(target).addInPlaceFromFloats(-4,11,8);
  (drift.emitter as Vector3).copyFrom(target).addInPlaceFromFloats(-5,.18,8);
  snow.direction1.set(1.2+gust,-1.9,.18);snow.direction2.set(2.5+gust*1.2,-1.1,.65);
  drift.direction1.set(1.8+gust,0,.25);drift.direction2.set(3.8+gust,0,.65);
  sun.intensity=1.72+.14*Math.sin(clock*.19);scene.fogDensity=.0105+gust*.0018;
  scene.fogColor=Color3.Lerp(new Color3(.28,.35,.40),new Color3(.34,.41,.46),gust*.35);
 },get active(){return snow.getActiveCount()+drift.getActiveCount();},capacity:snow.getCapacity()+drift.getCapacity()};
}
