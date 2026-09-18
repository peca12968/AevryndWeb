import json
from collections import Counter, defaultdict
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
blend=ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-cc0-scalp-overlay-r1091-study.blend"
out=ROOT / "assets-source" / "aevrynd-character" / "female-v249-mainline-r1091-top-projection.raw.json"
bpy.ops.wm.open_mainfile(filepath=str(blend))
scene=bpy.context.scene; scene.frame_set(1)
camera=scene.camera; camera.location=(0.0,-0.25,2.0); camera.data.lens=78
camera.rotation_euler=(Vector((0.0,0.015,1.51))-camera.location).to_track_quat('-Z','Y').to_euler()
hair=bpy.data.objects['AevryndFemaleGradedHairlineGroom_R1081']
family=hair.data.attributes['aevrynd_family_r1087']; radius=hair.data.attributes['radius']
result={}
for fam in (0,1,2,3,4):
    local_counts=Counter(); curve_hits=defaultdict(list); total=0
    for ci,curve in enumerate(hair.data.curves):
        if family.data[ci].value!=fam: continue
        for local in range(curve.points_length):
            pi=curve.first_point_index+local
            if radius.data[pi].value<=1e-9: continue
            world=hair.matrix_world @ hair.data.points[pi].position
            ndc=world_to_camera_view(scene,camera,world)
            # Rear-loop band seen above the scalp cap in the top render.
            if 0.20<=ndc.x<=0.80 and 0.52<=ndc.y<=0.68 and ndc.z>0:
                local_counts[local]+=1; curve_hits[ci].append(local); total+=1
    result[str(fam)]={'totalBandPoints':total,'localCounts':dict(sorted(local_counts.items())),
                      'curveCount':len(curve_hits),'examples':dict(list(curve_hits.items())[:30])}
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print('TOP_PROJECTION='+json.dumps(result,sort_keys=True))

