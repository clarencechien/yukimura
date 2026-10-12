"""Re-author clips on an existing baked kit without paying the texture bake cost."""
import bpy,sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from samurai_rig import bind_hero
from gltf_assets import share_images
root=Path(__file__).resolve().parent.parent
out=Path(os.environ.get('MODEL_OUTPUT',root/'public/models'))
source=Path(os.environ.get('MODEL_SOURCE',root/'assets/source/samurai-kit.blend'))
bpy.ops.wm.open_mainfile(filepath=str(source))
high_layers=[layer for layer in bpy.context.view_layer.layer_collection.children if layer.name.startswith('20_')]
for layer in high_layers:layer.exclude=True
report=json.loads((out/'manifest.json').read_text())
shared={}
for kind in report['variants']:
    mesh=bpy.data.objects[kind+'_runtime']
    old=mesh.parent;mesh.parent=None;mesh.location=(0,0,0)
    for mod in list(mesh.modifiers):
        if mod.type=='ARMATURE':mesh.modifiers.remove(mod)
    bpy.data.objects.remove(old,do_unlink=True)
    mesh.hide_set(False);mesh.hide_render=False
    rig=bind_hero(mesh,kind,reweight=False)
    if kind in ('yukimura','ieyasu'):mesh.data.materials[0].name='runtime/'+kind+' high bake'
    path=out/(kind+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
    shared.update(share_images(path));report['variants'][kind]['bytes']=path.stat().st_size
    rig.location=(0,3.5,0);rig.hide_render=True;mesh.hide_render=True
for layer in high_layers:layer.exclude=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
report['shared_textures']=shared;report['shared_texture_bytes']=sum(shared.values())
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
