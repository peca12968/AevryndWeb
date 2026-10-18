"""One explicit nominal corneal-thickness candidate; preserve geometry and stage."""
import bpy, json, hashlib, importlib.util
from pathlib import Path
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0009-optics'
SRC=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0008-a-tight-study.blend'
spec=importlib.util.spec_from_file_location('eyes',Path(__file__).with_name('build-female-next-r0006-native-eyes.py'))
stage=importlib.util.module_from_spec(spec); spec.loader.exec_module(stage); stage.E=E
bpy.ops.wm.open_mainfile(filepath=str(SRC)); s=bpy.context.scene
rig=bpy.data.objects['AFN_R0005_Rig']; stage.set_pose(rig,'neutral')
m=bpy.data.materials['AFN6_Cornea']; m.thickness_mode='SLAB'
out=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeOutputMaterial')
out.inputs['Thickness'].default_value=.00055
paths=[stage.render('a-slab-thickness',v,stage.helper_centres(),'neutral') for v in ('eyes','face','oblique')]
s['aevrynd_revision']='female-next-r0009-a-slab-thickness'
s['aevrynd_release_state']='OPTICAL_STUDY_VISUAL_REVIEW_PENDING'
bpy.context.preferences.filepaths.save_version=0
dest=SRC.parent/'aevrynd-female-next-r0009-a-slab-thickness-study.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
(E/'thickness-candidate.json').write_text(json.dumps({'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'hypothesis':'The open corneal dome needs an explicit thin-shell thickness for Eevee instead of its implicit spherical volume approximation.','geometryChanged':False,'thicknessM':.00055,'mode':'SLAB','renders':paths,'status':'VISUAL_REVIEW_PENDING'},indent=2)+'\n')
print('AFN_R0009_THICKNESS_DONE')
