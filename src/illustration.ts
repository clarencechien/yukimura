import {Scene} from '@babylonjs/core/scene';
import {Camera} from '@babylonjs/core/Cameras/camera';
import {PostProcess} from '@babylonjs/core/PostProcesses/postProcess';
import {Effect} from '@babylonjs/core/Materials/effect';
import {ExtractHighlightsPostProcess} from '@babylonjs/core/PostProcesses/extractHighlightsPostProcess';
import {BlurPostProcess} from '@babylonjs/core/PostProcesses/blurPostProcess';
import {Vector2} from '@babylonjs/core/Maths/math.vector';
import {Texture} from '@babylonjs/core/Materials/Textures/texture';

/** One display-space grade on touch devices. Desktop adds three quarter-size
 * native bloom stages; this same grade also merges them, without a second
 * full-screen resolve. ACES is applied upstream by Babylon materials. */
export function illustrationPass(scene:Scene,camera:Camera){
 const bloom=!matchMedia('(pointer:coarse)').matches;
 let highlights:ExtractHighlightsPostProcess|undefined;
 if(bloom){
  // A post-process size controls its INPUT. Keep scene capture full size;
  // extraction writes to blur-X's quarter-size input, and so on.
  highlights=new ExtractHighlightsPostProcess('winter highlights',1,camera,Texture.BILINEAR_SAMPLINGMODE);highlights.threshold=.70;
  new BlurPostProcess('winter bloom horizontal',new Vector2(1,0),9,.25,camera,Texture.BILINEAR_SAMPLINGMODE);
  new BlurPostProcess('winter bloom vertical',new Vector2(0,1),9,.25,camera,Texture.BILINEAR_SAMPLINGMODE);
 }
 Effect.ShadersStore['battleInkFragmentShader']=`
 precision highp float;
 varying vec2 vUV;
 uniform sampler2D textureSampler;
 #ifdef WINTER_BLOOM
 uniform sampler2D sceneSampler;
 #endif
 uniform vec2 texel;
 float lum(vec3 c){return dot(c,vec3(.2126,.7152,.0722));}
 vec3 sceneAt(vec2 uv){
 #ifdef WINTER_BLOOM
 return texture2D(sceneSampler,uv).rgb;
 #else
 return texture2D(textureSampler,uv).rgb;
 #endif
 }
 void main(){
  vec3 c=sceneAt(vUV);
  vec3 a=sceneAt(vUV+vec2(texel.x,0.)),b=sceneAt(vUV-vec2(texel.x,0.));
  vec3 d=sceneAt(vUV+vec2(0.,texel.y)),e=sceneAt(vUV-vec2(0.,texel.y));
  // Reuse the original five samples for restrained local contrast. Clamp to
  // neighbours to keep snow edges and spear silhouettes free of bright halos.
  vec3 lo=min(c,min(min(a,b),min(d,e))),hi=max(c,max(max(a,b),max(d,e)));
  c=clamp(c+(c-(a+b+d+e)*.25)*.16,lo,hi);
  float l=lum(c),key=smoothstep(.12,.78,l);
  c*=mix(vec3(.95,.987,1.045),vec3(1.038,1.012,.967),key);
  c=mix(vec3(lum(c)),c,1.045);
  c=(c-.40)*1.035+.40;
  float edge=smoothstep(.10,.35,length(vec2(lum(a)-lum(b),lum(d)-lum(e))));
  c*=1.-edge*.035;
 #ifdef WINTER_BLOOM
  c+=texture2D(textureSampler,vUV).rgb*.075;
 #endif
  float vignette=smoothstep(.28,.78,length(vUV-.5));
  gl_FragColor=vec4(clamp(c*(1.-vignette*.075),0.,1.),1.);
 }`;
 const pass=new PostProcess('winter film grade','battleInk',['texel'],bloom?['sceneSampler']:null,bloom?.25:1,camera,Texture.BILINEAR_SAMPLINGMODE,undefined,false,bloom?'#define WINTER_BLOOM':undefined);
 pass.onApply=effect=>{effect.setFloat2('texel',1/scene.getEngine().getRenderWidth(),1/scene.getEngine().getRenderHeight());if(highlights)effect.setTextureFromPostProcess('sceneSampler',highlights);};
 return pass;
}
