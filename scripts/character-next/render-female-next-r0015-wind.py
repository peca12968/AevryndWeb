"""Render actual baked diagnostic geometry; no full-groom motion is implied."""
import bpy,json,math,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
E=flow.R/'Evidence/character-female-next/r0015-guide-dynamics';proof=json.loads((E/'c-wind-blender-review.json').read_text());src=Path(proof['output']);assert flow.route.sha(src)==proof['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.threads_mode='FIXED';scene.render.threads=4;c=scene.camera;headZ=1.5624730926266572*.91;c.location=(.36,-.84,headZ+.02);c.rotation_euler=(Vector((0.,-.02,headZ))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;scene.render.resolution_x=scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';out=E/'wind-frames';out.mkdir(exist_ok=True)
paths=[]
for i in range(31):
    sample=i*24;scene.frame_set(sample+1);scene.render.filepath=str(out/f'wind-{i:03d}.png');bpy.ops.render.render(write_still=True);paths.append({'physicsSample':sample,'timeS':sample/240,'path':scene.render.filepath})
(E/'wind-render-frames.json').write_text(json.dumps({'sourceSha256':proof['outputSha256'],'frames':paths,'scope':'Actual 48-guide Blender diagnostic, physical/display radius 60 um, sampled at 10 fps for the GIF. Full native hair is hidden; 0 child fibres animated. The .blend retains all 240 Hz keys.'},indent=2)+'\n');print('AFN15_WIND_FRAMES_DONE',flush=True)
