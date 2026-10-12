import {Scene} from '@babylonjs/core/scene';
import {RawCubeTexture} from '@babylonjs/core/Materials/Textures/rawCubeTexture';
import {Constants} from '@babylonjs/core/Engines/constants';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {SphericalPolynomial} from '@babylonjs/core/Maths/sphericalPolynomial';
import {ImageProcessingConfiguration} from '@babylonjs/core/Materials/imageProcessingConfiguration';
import '@babylonjs/core/Materials/Textures/baseTexture.polynomial';
import '@babylonjs/core/Engines/Extensions/engine.rawTexture';

/** Small local sky reflection, no external HDRI downloads or frame-by-frame capture. */
export function winterReflections(scene:Scene){
 const size=64,faces:Uint8Array[]=[];
 const sun=new Vector3(.55,.8,-.5).normalize();
 for(let face=0;face<6;face++){
  const data=new Uint8Array(size*size*4);
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
   const u=2*(x+.5)/size-1,v=2*(y+.5)/size-1;
   const d=[new Vector3(1,-v,-u),new Vector3(-1,-v,u),new Vector3(u,1,v),new Vector3(u,-1,-v),new Vector3(u,-v,1),new Vector3(-u,-v,-1)][face].normalize();
   const sky=Math.max(0,d.y),ground=Math.max(0,-d.y),key=Math.pow(Math.max(0,Vector3.Dot(d,sun)),30);
   const cloud=.77+.23*Math.sin(d.x*9+d.z*4)*Math.sin(d.z*7-d.y*5);
   const horizon=Math.pow(1-Math.abs(d.y),6),rim=Math.pow(Math.max(0,d.x*.7+d.z*.7),12)*sky;
   const opening=Math.pow(Math.max(0,d.x*.2+d.y*.9-d.z*.4),6);
   const rgb=[.045+sky*.36*cloud+ground*.045+horizon*.13+key*.74+rim*.08+opening*.38,.058+sky*.45*cloud+ground*.042+horizon*.12+key*.61+rim*.15+opening*.40,.077+sky*.60*cloud+ground*.033+horizon*.11+key*.42+rim*.24+opening*.42];
   const i=(y*size+x)*4;for(let c=0;c<3;c++)data[i+c]=Math.round(Math.min(1,rgb[c])*255);data[i+3]=255;
  }faces.push(data);
 }
 const env=new RawCubeTexture(scene,faces,size,Constants.TEXTUREFORMAT_RGBA,Constants.TEXTURETYPE_UNSIGNED_BYTE,true,false,Constants.TEXTURE_TRILINEAR_SAMPLINGMODE);
 env.name='local-winter-sky';env.gammaSpace=false;
 // Low-frequency diffuse irradiance; directional highlights come from sun + cubemap.
 const sp=new SphericalPolynomial();sp.xx.set(.20,.24,.29);sp.yy.set(.20,.24,.29);sp.zz.set(.20,.24,.29);sp.y.set(.075,.09,.11);env.sphericalPolynomial=sp;
 scene.environmentTexture=env;scene.environmentIntensity=1;
 // Native material tone mapping, once, before our display-space grade.
 const image=scene.imageProcessingConfiguration;image.toneMappingEnabled=true;image.toneMappingType=ImageProcessingConfiguration.TONEMAPPING_ACES;image.exposure=1.35;image.contrast=1;image.applyByPostProcess=false;
}
