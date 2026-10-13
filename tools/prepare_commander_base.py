"""Regenerate a retargeting input from the editable kit without texture rebaking."""
from pathlib import Path
import hashlib
import bpy
from gltf_assets import share_images

def prepare(source:Path,snapshot:Path,stamp:Path):
    # Include the exporter recipe: the source contains 30 fps soldiers and
    # 90 fps commanders, regardless of the scene's last saved frame rate.
    digest=hashlib.sha256(source.read_bytes()).hexdigest()+':per-rig-fps-v2'
    if snapshot.exists() and stamp.exists() and stamp.read_text()==digest:return
    bpy.ops.wm.open_mainfile(filepath=str(source))
    for layer in bpy.context.view_layer.layer_collection.children:
        if layer.name.startswith('20_'):layer.exclude=True
    kind=snapshot.name.split('-')[0];mesh=bpy.data.objects[kind+'_runtime'];rig=mesh.parent
    rig.location=(0,0,0);mesh.hide_set(False);rig.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=mesh
    bpy.context.scene.render.fps=int(rig.get('animation_fps',90 if kind in ('yukimura','ieyasu') else 30))
    bpy.ops.export_scene.gltf(filepath=str(snapshot),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_vertex_color='ACTIVE',export_all_vertex_colors=False)
    share_images(snapshot);stamp.write_text(digest)
