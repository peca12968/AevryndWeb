"""Match alternate lighting, and locate fixed skin sites for display-tone auditing."""
import bpy,json,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0011-skin-brows';S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('stage',Path(__file__).with_name('build-female-next-r0007-socket-clearance.py'));stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage);stage.eyes.E=E
landmarks=json.loads((E/'skin-albedo-calibration.json').read_text())['samples'];records=[]
for label,name in [('baseline','aevrynd-female-next-r0010-c-spaced-lashes-study.blend'),('b-ridge-skin-brows','aevrynd-female-next-r0011-b-ridge-skin-brows-study.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(S/name));rig=bpy.data.objects['AFN_R0005_Rig'];stage.set_pose(rig,'neutral');fits=stage.eyes.helper_centres()
    scene=bpy.context.scene;stage.eyes.render(label+'-tone','face',fits,'neutral');sites=[]
    for x in landmarks:
        ndc=world_to_camera_view(scene,scene.camera,Vector(x['world']));sites.append([round(ndc.x*1100),round((1-ndc.y)*1100)])
    records.append({'label':label,'condition':'standard','image':str(E/(label+'-tone-face-neutral.png')),'skinReferencePixels':sites})
    key=bpy.data.objects['Aevrynd Key'];key.location=(-1.4,-2.,1.9);key.rotation_euler=(Vector((0,-.11,1.46))-key.location).to_track_quat('-Z','Y').to_euler();key.data.size=.8;bpy.data.objects['Aevrynd Fill'].data.energy=195.
    for view in ('face','eyes'):records.append({'label':label,'condition':'alternate-light','image':stage.eyes.render(label+'-alternate-light',view,fits,'neutral')})
(E/'controlled-review.json').write_text(json.dumps({'sourceFilesUnchanged':True,'alternateLight':'Same settings for both sources; not saved to either asset.','records':records},indent=2)+'\n');print('AFN_R0011_REVIEW_DONE')
