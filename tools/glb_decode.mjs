/** Decode a Draco + WebP GLB from glb_compress.sh back into a plain one (no compression extensions, PNG
 *  textures), e.g. for Blender builds without Draco. Needs the gltf-transform packages:
 *    npm install --no-save @gltf-transform/cli@4.1.1 && node tools/glb_decode.mjs in.glb out.glb
 */
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { textureCompress } from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';
import sharp from 'sharp';
const [src, dst] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'draco3d.decoder': await draco3d.createDecoderModule() });
const doc = await io.read(src);
for (const e of doc.getRoot().listExtensionsUsed()) if (e.extensionName === 'KHR_draco_mesh_compression') e.dispose();
await doc.transform(textureCompress({ encoder: sharp, targetFormat: 'png' }));
for (const e of doc.getRoot().listExtensionsUsed()) if (e.extensionName === 'EXT_texture_webp') e.dispose();
await io.write(dst, doc);
