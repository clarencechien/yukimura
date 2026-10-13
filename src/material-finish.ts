import {Scene} from '@babylonjs/core/scene';
import {AbstractMesh} from '@babylonjs/core/Meshes/abstractMesh';
import {PBRMaterial} from '@babylonjs/core/Materials/PBR/pbrMaterial';
import {Texture} from '@babylonjs/core/Materials/Textures/texture';

const surfaceDetails=new WeakMap<Scene,{forged:Texture;woven:Texture}>();
function sharedDetails(scene:Scene){
 let maps=surfaceDetails.get(scene);
 if(!maps){
  const make=(name:string,repeat:number)=>{const t=new Texture(`${import.meta.env.BASE_URL}look/${name}-detail.png?rev=16`,scene,false,false);t.gammaSpace=false;t.uScale=t.vScale=repeat;return t;};
  maps={forged:make('forged',12),woven:make('woven',4)};surfaceDetails.set(scene,maps);
 }
 return maps;
}

/** Reuse baked AO. Only the two commanders pay for a masked lacquer lobe. */
export function finishMaterials(scene:Scene,meshes:AbstractMesh[],kind:string,details=true){
 const materials=new Set(meshes.map(mesh=>mesh.material));
 for(const material of materials){
  if(!(material instanceof PBRMaterial))continue;
  material.maxSimultaneousLights=4;material.environmentIntensity=.95;material.enableSpecularAntiAliasing=true;
  material.ambientTexture=material.metallicTexture;material.useAmbientInGrayScale=true;material.ambientTextureStrength=.42;material.ambientTextureImpactOnAnalyticalLights=0;
  if(details&&!material.name.startsWith('samurai woven')){
   const maps=sharedDetails(scene),cloth=material.name==='commander deerskin and cloth';
   material.detailMap.isEnabled=true;material.detailMap.texture=cloth?maps.woven:maps.forged;
   material.detailMap.diffuseBlendLevel=.55;material.detailMap.roughnessBlendLevel=.55;material.detailMap.bumpLevel=cloth?.65:.4;
  }
  if((kind==='yukimura'||kind==='ieyasu')&&material.name.startsWith('runtime/')){
   const coat=new Texture(`${import.meta.env.BASE_URL}look/${kind}-coat.png?rev=commander-14`,scene,false,false);coat.gammaSpace=false;
   material.clearCoat.isEnabled=true;material.clearCoat.intensity=.55;material.clearCoat.roughness=1;material.clearCoat.texture=coat;
  }
 }
}
