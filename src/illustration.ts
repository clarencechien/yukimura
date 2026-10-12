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
  float edge=smoothstep(.07,.28,length(vec2(a-b,d-e)));
  vec3 ink=vec3(.035,.060,.083),paper=vec3(.94,.89,.77);
  vec3 toned=mix(ink,c,smoothstep(.0,.22,l));
  toned=mix(toned,paper,smoothstep(.68,1.,l)*.20);
  // Preserve vermilion and the warm key/cool shadow separation. A light ink
  // accent should not turn distant, animated armour into black cardboard.
  toned*=1.-edge*.17;
  float fiber=(grain(floor(gl_FragCoord.xy))-.5)*.010;
  float vignette=smoothstep(.20,.77,length(vUV-.5));
  gl_FragColor=vec4(toned*(1.-vignette*.17)+fiber,1.);
 }`;
 const pass=new PostProcess('battle ink','battleInk',['texel'],null,1,camera);
 pass.onApply=effect=>effect.setFloat2('texel',1/scene.getEngine().getRenderWidth(),1/scene.getEngine().getRenderHeight());
 return pass;
}
