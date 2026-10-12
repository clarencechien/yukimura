import {Scene} from '@babylonjs/core/scene';
import {Camera} from '@babylonjs/core/Cameras/camera';
import {PostProcess} from '@babylonjs/core/PostProcesses/postProcess';
import {Effect} from '@babylonjs/core/Materials/effect';

/** Dry pigment, restrained ink edges and a cool-shadow/warm-paper palette. */
export function illustrationPass(scene:Scene,camera:Camera){
 Effect.ShadersStore['battleInkFragmentShader']=`
 precision highp float;
 varying vec2 vUV;
 uniform sampler2D textureSampler;
 uniform vec2 texel;
 float lum(vec3 c){return dot(c,vec3(.2126,.7152,.0722));}
 float grain(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
 void main(){
  vec3 c=texture2D(textureSampler,vUV).rgb;
  float l=lum(c);
  float a=lum(texture2D(textureSampler,vUV+vec2(texel.x,0.)).rgb);
  float b=lum(texture2D(textureSampler,vUV-vec2(texel.x,0.)).rgb);
  float d=lum(texture2D(textureSampler,vUV+vec2(0.,texel.y)).rgb);
  float e=lum(texture2D(textureSampler,vUV-vec2(0.,texel.y)).rgb);
  float edge=smoothstep(.045,.20,length(vec2(a-b,d-e)));
  vec3 ink=vec3(.055,.085,.105),paper=vec3(.86,.85,.77);
  vec3 toned=mix(ink,c,smoothstep(.0,.25,l));
  toned=mix(toned,paper,smoothstep(.60,1.,l)*.28);
  toned=mix(vec3(l),toned,.89);
  toned*=1.-edge*.42;
  float fiber=(grain(floor(gl_FragCoord.xy))-.5)*.024;
  float vignette=smoothstep(.20,.77,length(vUV-.5));
  gl_FragColor=vec4(toned*(1.-vignette*.17)+fiber,1.);
 }`;
 const pass=new PostProcess('battle ink','battleInk',['texel'],null,1,camera);
 pass.onApply=effect=>effect.setFloat2('texel',1/scene.getEngine().getRenderWidth(),1/scene.getEngine().getRenderHeight());
 return pass;
}
