"""Locate residual patch intersections and cross-check negative distances by ray parity.

The source has two eye boundaries. Parity is a diagnostic vote only, never a
certificate of solid containment or full strand collision.
"""
import bpy, json
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0004-surface-conforming'
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0004-b-relaxed-study.blend'))
scene=bpy.context.scene;scene.frame_set(1);body=bpy.data.objects['AevryndFemaleNextPerioral_R0004']
dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);m=ev.to_mesh();verts=[ev.matrix_world@v.co for v in m.vertices];m.calc_loop_triangles();tris=[tuple(t.vertices) for t in m.loop_triangles];tree=BVHTree.FromPolygons(verts,tris,all_triangles=True)
local=[t for t in tris if all(abs(verts[i].x)<.065 and 1.34<verts[i].z<1.43 and verts[i].y<-.07 for i in t)];ltree=BVHTree.FromPolygons(verts,local,all_triangles=True);pairs=[(a,b) for a,b in ltree.overlap(ltree) if a<b and set(local[a]).isdisjoint(local[b])]
centres=[sum((verts[i] for i in local[t]),Vector())/3 for pair in pairs for t in pair]
pair_bounds=[[min(p[axis] for p in centres),max(p[axis] for p in centres)] for axis in range(3)] if centres else None
hair=bpy.data.objects['AevryndFemaleGradedHairlineGroom_R1081'].evaluated_get(dg);negative=[]
for i,point in enumerate(hair.data.points):
 p=hair.matrix_world@point.position;h=tree.find_nearest(p);signed=(p-h[0]).dot(h[1].normalized())
 if signed<0:negative.append((i,p,signed))
directions=[Vector(v).normalized() for v in ((1.,0.,0.),(-1.,0.,0.),(0.,1.,0.),(0.,-1.,0.))]
def ray_count(origin,direction):
 p=origin.copy();count=0
 for step in range(80):
  hit=tree.ray_cast(p,direction,3.)
  if hit[0] is None:return count
  count+=1;p=hit[0]+direction*.000002
 return None
counts=Counter();samples=[]
for i,p,signed in negative:
 rays=[ray_count(p,d) for d in directions]
 if any(v is None for v in rays):verdict='iteration-limit'
 else:
  odd=sum(n%2 for n in rays);verdict='inside-majority' if odd>=3 else ('outside-majority' if odd<=1 else 'disagreed')
 counts[verdict]+=1
 if len(samples)<20:samples.append({'point':i,'world':list(p),'nearestSignedM':signed,'rayCounts':rays,'diagnosticVote':verdict})
ev.to_mesh_clear()
# Locate contacts against the unsmoothed, posed control cage.
sub=next(mod for mod in body.modifiers if mod.type=='SUBSURF');sub.show_viewport=False;dg.update();ev=body.evaluated_get(dg);cage=ev.to_mesh();cv=[ev.matrix_world@v.co for v in cage.vertices];ctree=BVHTree.FromPolygons(cv,[tuple(p.vertices) for p in cage.polygons]);bands=Counter()
names=('skin10','skin25','skin45','skin65','skin85','vermilion','roll','margin','inner','vestibule','cavity','rear')
for p in centres:
 idx=ctree.find_nearest(p)[2]
 if idx<12595:bands['retained-source']+=1
 else:
  band=(idx-12595)//74;bands[names[band] if band<len(names) else 'rear-cap']+=1
ev.to_mesh_clear()
result={'revision':'female-next-r0004','variant':'b-relaxed','mouthNonAdjacentPairs':len(pairs),'contactCentroidBoundsM':pair_bounds,'nearestControlCageBandObservations':dict(bands),'negativeNearestHairPoints':len(negative),'parityVoteCounts':dict(counts),'samples':samples,'limits':['Horizontal ray votes on an eye-open body are supporting diagnostics, not a watertight solid certificate.','An inside-majority point still requires geometric investigation; outside-majority does not establish segment/radius safety.','Band assignment uses nearest unsmoothed faces and is approximate.']}
(E/'residual-collision-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))
