"""Controlled whole-face, bounded gaze and alternate-light reviews of saved optics."""
import bpy, math, json, importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0009-optics'; S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('eyes',Path(__file__).with_name('build-female-next-r0006-native-eyes.py'))
stage=importlib.util.module_from_spec(spec); spec.loader.exec_module(stage); stage.E=E
rows=[]
for label,filename in [('baseline','aevrynd-female-next-r0008-a-tight-study.blend'),('a-slab-thickness','aevrynd-female-next-r0009-a-slab-thickness-study.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(S/filename)); rig=bpy.data.objects['AFN_R0005_Rig']; stage.set_pose(rig,'neutral'); fits=stage.helper_centres()
    if label=='baseline':
        for v in ('face','oblique'): rows.append({'label':label,'condition':'standard','image':stage.render(label,v,fits,'neutral')})
    else:
        for pose,angle in [('gaze-left',10),('gaze-right',-10)]:
            stage.set_pose(rig,'neutral')
            for side in ('L','R'): rig.pose.bones['eye.'+side].rotation_euler[2]=math.radians(angle)
            bpy.context.view_layer.update()
            rows.append({'label':label,'condition':pose,'image':stage.render(label,'eyes',fits,pose)})
    stage.set_pose(rig,'neutral')
    key=bpy.data.objects['Aevrynd Key']; key.location=(-1.4,-2.,1.9)
    key.rotation_euler=(Vector((0.,-.11,1.46))-key.location).to_track_quat('-Z','Y').to_euler(); key.data.size=.8
    bpy.data.objects['Aevrynd Fill'].data.energy=195.
    rows.append({'label':label,'condition':'alternate-light','image':stage.render(label+'-alternate-light','eyes',fits,'neutral'),
                 'keyLocation':list(key.location),'keyEnergy':key.data.energy,'keySize':key.data.size,'fillEnergy':195.})
(E/'controlled-review.json').write_text(json.dumps({'scope':'Review renders only. Alternate light is never saved to the model and compared within identical alternate lighting.','renders':rows},indent=2)+'\n')
print('AFN_R0009_REVIEW_DONE')
