"""Only paired profile and second-light head views of the retained art candidate."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0096-artist-bob-foundation';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r96views',Path(__file__).with_name('render-female-next-r0091-matched.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);v.E=E
tick=time.time();rows={};ref=json.loads((E/'a-build-summary.json').read_text(encoding='utf8'))
for tag,path in [('baseline',S/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend'),('a-artist-Bob',Path(ref['output']))]:
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();rows[tag]=[v.image(tag,'profile')];lights=[(o,o.matrix_world.copy()) for o in bpy.context.scene.objects if o.type=='LIGHT']
 for o,mat in lights:o.location.x=-o.location.x;o.rotation_euler=(Vector(v.m.rig.k.b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.context.view_layer.update();row=v.image(tag+'-second-light','oblique');row['evidenceView']='second-light-oblique';rows[tag].append(row)
 for o,mat in lights:o.matrix_world=mat
 bpy.context.view_layer.update();(E/'affected-view-controls.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
for a,b in zip(rows['baseline'],rows['a-artist-Bob']):assert {k:x for k,x in a.items() if k!='file'}=={k:x for k,x in b.items() if k!='file'}
print('R96_PAIRED_PROFILE_SECOND_LIGHT_DONE',time.time()-tick,flush=True)
