import json,sys,math,hashlib,struct
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree

path=sys.argv[sys.argv.index('--')+1]

def signature(obj):
    digest=hashlib.sha256();digest.update(struct.pack('<II',len(obj.data.vertices),len(obj.data.polygons)))
    for v in obj.data.vertices:digest.update(struct.pack('<fff',*v.co))
    for p in obj.data.polygons:
        digest.update(struct.pack('<I',len(p.vertices)))
        for index in p.vertices:digest.update(struct.pack('<I',index))
    return digest.hexdigest()

baseline_path=Path(path).resolve().parent/'aevrynd-female-authoring-v39.blend'
bpy.ops.wm.open_mainfile(filepath=str(baseline_path));baseline={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=path)
scene=bpy.context.scene; failures=[]
candidate={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH'};changed={'Lip_Upper','Lip_Lower','Mouth_WetLine'};added={'Mouth_OralCavity','Mouth_UpperTeeth','Mouth_Tongue'}
if set(candidate)!=set(baseline)|added:failures.append('candidate mesh set is not v39 plus three oral layers')
unexpected=[n for n,h in baseline.items() if n not in changed and candidate.get(n)!=h]
if unexpected:failures.append('unexpected geometry changes: '+','.join(unexpected))
required={'Lip_Upper':'upper_lip_volume','Lip_Lower':'lower_lip_volume','Mouth_WetLine':'mouth_wet_margin','Mouth_OralCavity':'oral_cavity_cup','Mouth_UpperTeeth':'upper_teeth','Mouth_Tongue':'tongue'}
for name,role in required.items():
    obj=bpy.data.objects.get(name)
    if not obj or obj.get('aevrynd_role')!=role:failures.append(name+' layer/role missing')
    elif obj.parent_type!='BONE' or obj.parent_bone!='head':failures.append(name+' head binding invalid')

def tree(obj,deps):
    ev=obj.evaluated_get(deps);mesh=ev.to_mesh();pts=[ev.matrix_world@v.co for v in mesh.vertices];faces=[tuple(p.vertices) for p in mesh.polygons]
    result=BVHTree.FromPolygons(pts,faces,all_triangles=False);ev.to_mesh_clear();return result

frames={}; pairs=[('Lip_Upper','AevryndFemaleBodyBase'),('Lip_Lower','AevryndFemaleBodyBase'),('Mouth_WetLine','Lip_Upper'),('Mouth_WetLine','Lip_Lower'),('Mouth_UpperTeeth','AevryndFemaleBodyBase'),('Mouth_Tongue','AevryndFemaleBodyBase'),('Mouth_OralCavity','AevryndFemaleBodyBase')]
for frame in (1,20):
    scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get();vals={}
    for a,b in pairs:
        count=len(tree(bpy.data.objects[a],deps).overlap(tree(bpy.data.objects[b],deps)));vals[a+'__'+b]=count
        if count:failures.append(f'frame {frame} {a}/{b} {count} overlaps')
    frames[str(frame)]=vals
nonfinite=sum(not all(math.isfinite(x) for x in v.co) for o in bpy.data.objects if o.type=='MESH' for v in o.data.vertices)
if nonfinite:failures.append(f'{nonfinite} nonfinite vertices')
report={'unchanged_baseline_meshes':sum(candidate.get(n)==h for n,h in baseline.items() if n not in changed),'frames':frames,'nonfinite':nonfinite,'objects':{n:{'vertices':len(bpy.data.objects[n].data.vertices),'faces':len(bpy.data.objects[n].data.polygons)} for n in required}}
print('AEVRYND_MOUTH_V40_AUDIT='+json.dumps(report))
if failures:raise SystemExit('; '.join(failures))
