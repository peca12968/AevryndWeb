"""Review the saved, collision-qualified candidate without resaving its geometry."""
import bpy,json,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0010-eye-rim'
spec=importlib.util.spec_from_file_location('stage',Path(__file__).with_name('build-female-next-r0007-socket-clearance.py'));stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage);stage.eyes.E=E
source=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0010-c-spaced-lashes-study.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['AFN_R0005_Rig'];fits=stage.eyes.helper_centres();images=[]
for pose,view in [('neutral','profile'),('gaze-left','eyes'),('turn-right','face')]:
    stage.set_pose(rig,pose);images.append(stage.eyes.render('c-spaced-lashes',view,fits,pose))
stage.set_pose(rig,'neutral');key=bpy.data.objects['Aevrynd Key'];key.location=(-1.4,-2.,1.9);key.rotation_euler=(Vector((0.,-.11,1.46))-key.location).to_track_quat('-Z','Y').to_euler();key.data.size=.8;bpy.data.objects['Aevrynd Fill'].data.energy=195.
images.append(stage.eyes.render('c-spaced-lashes-alternate-light','eyes',fits,'neutral'))
(E/'controlled-review.json').write_text(json.dumps({'source':str(source),'renders':images,'alternateLight':'Matches r0009 alternate-light setup; review-only, not saved to the asset.','sourceModified':False},indent=2)+'\n')
print('AFN_R0010_REVIEW_DONE')
