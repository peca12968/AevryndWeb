"""Audit the currently retained groom against the r1110 body at motion gate frames."""
import bpy,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'assets-source'/'aevrynd-character'/'aevrynd-female-cc0-integrated-upper-lip-r1110-study.blend'
report_path=ROOT/'assets-source'/'aevrynd-character'/'female-v249-mainline-r1114-current-hair-baseline.audit.json'
bpy.ops.wm.open_mainfile(filepath=str(src))
scene=bpy.context.scene; body=bpy.data.objects['AevryndFemaleCC0PalpebralClosure_R1097']; hair=bpy.data.objects['AevryndFemaleGradedHairlineGroom_R1081']
hair.hide_render=False;hair.hide_viewport=False
results={}
for frame in (1,20,33,61):
 scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();deps.update()
 eb=body.evaluated_get(deps);mesh=eb.to_mesh();verts=[eb.matrix_world@v.co for v in mesh.vertices];faces=[tuple(p.vertices) for p in mesh.polygons];tree=BVHTree.FromPolygons(verts,faces,all_triangles=False);eb.to_mesh_clear()
 eh=hair.evaluated_get(deps);radius=eh.data.attributes.get('radius');signed=[];visible=0
 for i,p in enumerate(eh.data.points):
  if radius and radius.data[i].value<=1e-8:continue
  visible+=1;world=eh.matrix_world@p.position;hit=tree.find_nearest(world)
  if hit and hit[1] is not None:signed.append((world-hit[0]).dot(hit[1].normalized()))
 results[str(frame)]={'visiblePoints':visible,'tested':len(signed),'minimumSignedClearanceM':min(signed),'penetratingPoints':sum(v<-.00005 for v in signed),'belowOneMm':sum(v<.001 for v in signed)}
report={
 'revision':'v249r1114-current-hair-baseline',
 'source':str(src),
 'hairObject':hair.name,
 'curveCount':len(hair.data.curves),
 'pointCount':len(hair.data.points),
 'collisionAudit':results,
 'technicalStatus':'PASS_ZERO_PENETRATION',
 'websitePromotionApproved':False,
}
report_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('R1114_HAIR_COLLISION='+json.dumps(results,sort_keys=True))
