import {Scene} from '@babylonjs/core/scene';
import {AbstractMesh} from '@babylonjs/core/Meshes/abstractMesh';
import {PBRMaterial} from '@babylonjs/core/Materials/PBR/pbrMaterial';
import {Texture} from '@babylonjs/core/Materials/Textures/texture';

/** Reuse baked AO. Only the two commanders pay for a masked lacquer lobe. */
export function finishMaterials(scene:Scene,meshes:AbstractMesh[],kind:string){
 const materials=new Set(meshes.map(mesh=>mesh.material));
 for(const material of materials){
  if(!(material instanceof PBRMaterial))continue;
  material.maxSimultaneousLights=4;material.environmentIntensity=.95;material.enableSpecularAntiAliasing=true;
  material.ambientTexture=material.metallicTexture;material.useAmbientInGrayScale=true;material.ambientTextureStrength=.42;material.ambientTextureImpactOnAnalyticalLights=0;
  if(kind==='yukimura'||kind==='ieyasu'){
   const coat=new Texture(`${import.meta.env.BASE_URL}look/${kind}-coat.png?rev=light-11`,scene,false,false);coat.gammaSpace=false;
   material.clearCoat.isEnabled=true;material.clearCoat.intensity=.55;material.clearCoat.roughness=1;material.clearCoat.texture=coat;
  }
 }
}
