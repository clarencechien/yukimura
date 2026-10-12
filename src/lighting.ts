import {Scene} from '@babylonjs/core/scene';
import {RawCubeTexture} from '@babylonjs/core/Materials/Textures/rawCubeTexture';
import {Constants} from '@babylonjs/core/Engines/constants';
import {Vector3} from '@babylonjs/core/Maths/math.vector';
import {SphericalPolynomial} from '@babylonjs/core/Maths/sphericalPolynomial';
import '@babylonjs/core/Materials/Textures/baseTexture.polynomial';
import '@babylonjs/core/Engines/Extensions/engine.rawTexture';

/** Small local sky reflection, no external HDRI downloads or frame-by-frame capture. */
export function winterReflections(scene:Scene){
 const size=32,faces:Uint8Array[]=[];
 const sun=new Vector3(-.5,.7,-.5).normalize();
 for(let face=0;face<6;face++){
  const data=new Uint8Array(size*size*4);
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
   const u=2*(x+.5)/size-1,v=2*(y+.5)/size-1;
   const d=[new Vector3(1,-v,-u),new Vector3(-1,-v,u),new Vector3(u,1,v),new Vector3(u,-1,-v),new Vector3(u,-v,1),new Vector3(-u,-v,-1)][face].normalize();
   const sky=Math.max(0,d.y),ground=Math.max(0,-d.y),key=Math.pow(Math.max(0,Vector3.Dot(d,sun)),42);
   const rgb=[.19+sky*.30+ground*.14+key*.60,.23+sky*.38+ground*.12+key*.49,.28+sky*.47+ground*.09+key*.34];
   const i=(y*size+x)*4;for(let c=0;c<3;c++)data[i+c]=Math.round(Math.min(1,rgb[c])*255);data[i+3]=255;
  }faces.push(data);
 }
 const env=new RawCubeTexture(scene,faces,size,Constants.TEXTUREFORMAT_RGBA,Constants.TEXTURETYPE_UNSIGNED_BYTE,true,false,Constants.TEXTURE_TRILINEAR_SAMPLINGMODE);
 env.name='local-winter-sky';env.gammaSpace=false;
 // Low-frequency diffuse irradiance; directional highlights come from sun + cubemap.
 const sp=new SphericalPolynomial();sp.xx.set(.30,.35,.40);sp.yy.set(.30,.35,.40);sp.zz.set(.30,.35,.40);env.sphericalPolynomial=sp;
 scene.environmentTexture=env;scene.environmentIntensity=.8;
}
