"""Compare only the pre-cut and current perioral surface under fixed lighting."""
import bpy, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0004-surface-conforming'
S=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0001-baseline.blend'
E.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(S))
BODY='AevryndFemaleCC0PalpebralClosure_R1097';DONOR='AevryndFemaleCC0Baseline_v259'
def mixed(o):
 K=o.data.shape_keys.key_blocks;P=[v.co.copy() for v in K[0].data]
 for k in K[1:]:
  if k.mute:continue
  for i,v in enumerate(k.data):P[i]+=k.value*(v.co-k.relative_key.data[i].co)
 return P
def render(label,view):
 scene=bpy.context.scene;scene.frame_set(1);cam=scene.camera
 views={'face':((0.,-.64,1.47),(0.,-.035,1.445),100,(1200,1000)), 'mouth':((0.,-.43,1.391),(0.,-.115,1.386),135,(1100,720)), 'mouth-oblique':((.105,-.43,1.391),(0.,-.115,1.386),135,(1100,720))}
 cam.location,target,cam.data.lens,size=views[view];cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100;scene.render.filepath=str(E/f'{label}-{view}.png');bpy.ops.render.render(write_still=True)
body=bpy.data.objects[BODY];donor=bpy.data.objects[DONOR]
results=[]
for obj,label in ((body,'current'),(donor,'precut-donor')):
 body.hide_render=True;donor.hide_render=True;obj.hide_render=False
 for view in ('face','mouth','mouth-oblique'):render(label,view)
 coords=mixed(obj);tree=BVHTree.FromPolygons(coords,[tuple(p.vertices) for p in obj.data.polygons])
 rows=[]
 for x in (0.,.008,.016,.024,.032,.040):
  row=[]
  for z in (1.374,1.380,1.3862,1.392,1.398,1.404):
   hit=tree.ray_cast(Vector((x,-.3,z)),Vector((0.,1.,0.)),.32)
   row.append({'z':z,'y':hit[0].y if hit[0] else None,'face':hit[2]})
  rows.append({'x':x,'rays':row})
 results.append({'object':obj.name,'rows':rows,'groupLipsVertices':sum(any(g.group==obj.vertex_groups['lips'].index for g in v.groups) for v in obj.data.vertices)})
(E/'source-surface-probes.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8');print(json.dumps(results,indent=2))
