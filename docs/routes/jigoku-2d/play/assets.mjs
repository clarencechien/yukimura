export const HERO_PARTS=['rearFoot','frontFoot','rearShin','frontShin','rearThigh','frontThigh','lower','rearUpper','frontUpper','torso','rearFore','frontFore','rearHand','frontHand'];
export const ENEMY_PARTS=['leftFoot','rightFoot','leftShin','rightShin','leftThigh','rightThigh','lower','torso'];
export const FILES=['arena.webp','guard-rig.json','thrust-rig.json','enemy-rig.json','ghost-warrior.webp','guard-yari.webp',...HERO_PARTS.map(p=>`hero-${p}.webp`),...ENEMY_PARTS.map(p=>`enemy-body-${p}.webp`),...['upper','fore','grip','katana'].map(p=>`enemy-${p}.webp`)];
export const assetURL=name=>window.SANADA_ASSETS?.[name]??`../combat/${name}`;
