import bpy,hashlib,struct,json,sys,math
from pathlib import Path
from mathutils.bvhtree import BVHTree

candidate_path=Path(sys.argv[sys.argv.index('--')+1]).resolve();baseline_path=candidate_path.parent/'aevrynd-female-authoring-v41.blend'
def sig(o):
 d=hashlib.sha256();d.update(struct.pack('<II',len(o.data.vertices),len(o.data.polygons)))
 for v in o.data.vertices:d.update(struct.pack('<fff',*v.co))
 for p in o.data.polygons:
  d.update(struct.pack('<I',len(p.vertices)))
  for i in p.vertices:d.update(struct.pack('<I',i))
 return d.hexdigest()
def snap(path):bpy.ops.wm.open_mainfile(filepath=str(path));return {o.name:sig(o) for o in bpy.data.objects if o.type=='MESH'}
base=snap(baseline_path);candidate=snap(candidate_path);fail=[];changed={'HairMain','HairGuides','HairFlyaways'}
if set(candidate)!=set(base):fail.append('mesh set changed')
unexpected=[n for n,h in base.items() if n not in changed and candidate.get(n)!=h]
if unexpected:fail.append('unexpected geometry: '+','.join(unexpected))
scene=bpy.context.scene
def tree(o,deps):
 ev=o.evaluated_get(deps);m=ev.to_mesh();pts=[ev.matrix_world@v.co for v in m.vertices];faces=[tuple(p.vertices) for p in m.polygons];t=BVHTree.FromPolygons(pts,faces,all_triangles=False);ev.to_mesh_clear();return t
frames={}
for frame in (1,20):
 scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();body=tree(bpy.data.objects['AevryndFemaleBodyBase'],deps);scalp=tree(bpy.data.objects['HairScalp'],deps);large=tree(bpy.data.objects['HairClumpsLarge'],deps);medium=tree(bpy.data.objects['HairClumpsMediumCards'],deps)
 vals={'main_body':len(tree(bpy.data.objects['HairMain'],deps).overlap(body)),'guides_body':len(tree(bpy.data.objects['HairGuides'],deps).overlap(body)),'flyaways_body':len(tree(bpy.data.objects['HairFlyaways'],deps).overlap(body)),'large_body':len(large.overlap(body)),'medium_body':len(medium.overlap(body)),'large_scalp':len(large.overlap(scalp)),'medium_scalp':len(medium.overlap(scalp)),'large_medium':len(large.overlap(medium))};frames[str(frame)]=vals
 for n,c in vals.items():
  if c:fail.append(f'frame {frame} {n} {c}')
removed={n:int(bpy.data.objects[n].get('aevrynd_removed_tail_fibers',0)) for n in changed};expected={'HairMain':309,'HairGuides':6,'HairFlyaways':3}
if removed!=expected:fail.append('removed fiber counts invalid')
nonfinite=sum(not all(math.isfinite(x) for x in v.co) for o in bpy.data.objects if o.type=='MESH' for v in o.data.vertices)
if nonfinite:fail.append(f'nonfinite {nonfinite}')
report={'unchanged_baseline_meshes':sum(candidate.get(n)==h for n,h in base.items() if n not in changed),'removed_tail_fibers':removed,'frames':frames,'nonfinite':nonfinite}
print('AEVRYND_GROOM_V42_AUDIT='+json.dumps(report))
if fail:raise SystemExit('; '.join(fail))
