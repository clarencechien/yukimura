import {Scene} from '@babylonjs/core/scene';
import {PBRMaterial} from '@babylonjs/core/Materials/PBR/pbrMaterial';
import {Texture} from '@babylonjs/core/Materials/Textures/texture';
import {Color3} from '@babylonjs/core/Maths/math.color';

/** Shared static textures: snow is rough, meltwater catches the winter sky. */
export function weatheredMaterial(scene:Scene,kind:string,name=kind){
 const m=new PBRMaterial(name,scene);m.metallic=1;m.roughness=1;
 const texture=(suffix:string,linear=false)=>{const t=new Texture(`${import.meta.env.BASE_URL}environment/${kind}-${suffix}.png?rev=winter-1`,scene);t.gammaSpace=!linear;t.anisotropicFilteringLevel=4;return t;};
 m.albedoTexture=texture('color');m.bumpTexture=texture('normal',true);m.metallicTexture=texture('surface',true);
 m.useRoughnessFromMetallicTextureAlpha=false;m.useRoughnessFromMetallicTextureGreen=true;m.useMetallnessFromMetallicTextureBlue=true;
 m.environmentIntensity=.65;m.maxSimultaneousLights=4;m.albedoColor=Color3.White();
 return m;
}
export function weatheredMaterials(scene:Scene){
 return {snow:weatheredMaterial(scene,'snow'),wood:weatheredMaterial(scene,'wood'),stone:weatheredMaterial(scene,'stone'),paper:weatheredMaterial(scene,'plaster'),dark:weatheredMaterial(scene,'roof')};
}
