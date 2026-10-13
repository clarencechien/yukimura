"""Fast control-rig check before regenerating the 92-bone deformation exports."""
from pathlib import Path
import sys,bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from samurai_rig import bind_hero
from gltf_assets import share_images
root=Path(__file__).resolve().parent.parent;out=root/'.tmp/wrist-probe';out.mkdir(exist_ok=True)
for kind in sys.argv[1:] or ['yukimura','ieyasu']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=90
 bpy.ops.import_scene.gltf(filepath=str(root/'.tmp/fullbody-v14'/f'{kind}-v13.glb'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent==rig)
 mesh.parent=None
 for mod in list(mesh.modifiers):
  if mod.type=='ARMATURE':mesh.modifiers.remove(mod)
 bpy.data.objects.remove(rig,do_unlink=True)
 rig=bind_hero(mesh,kind,reweight=False,natural_wrists=True)
 bpy.ops.export_scene.gltf(filepath=str(out/f'{kind}.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True)
 share_images(out/f'{kind}.glb')
