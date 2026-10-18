"""Reopen optical studies, verify native-body preservation, and localize collisions."""
import bpy, json, math, hashlib, array
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0006-native-eyes';S=R/'engine/assets/characters/female-next/source'
def mesh_hash(mesh):
 h=hashlib.sha256();a=array.array('f',[0.]*(len(mesh.vertices)*3));mesh.vertices.foreach_get('co',a);h.update(a.tobytes());b=array.array('i',[0]*len(mesh.loops));mesh.loops.foreach_get('vertex_index',b);h.update(b.tobytes());return h.hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0005-native-source.blend'))
source_hash=mesh_hash(bpy.data.objects['AFN_R0005_Body'].data)
source_bones={b.name:[list(row) for row in b.matrix_local] for b in bpy.data.objects['AFN_R0005_Rig'].data.bones}
result=[]
for label in ('a-recessed','b-balanced','c-full'):
 path=S/f'aevrynd-female-next-r0006-{label}-study.blend';bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['AFN_R0005_Body'];rig=bpy.data.objects['AFN_R0005_Rig'];dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);m=ev.to_mesh();V=[ev.matrix_world@v.co for v in m.vertices];m.calc_loop_triangles();T=[tuple(t.vertices) for t in m.loop_triangles];tree=BVHTree.FromPolygons(V,T,all_triangles=True)
 control=BVHTree.FromPolygons([body.matrix_world@v.co for v in body.data.vertices],[tuple(p.vertices) for p in body.data.polygons]);parts=[];localization={}
 for obj in sorted((o for o in bpy.data.objects if o.name.startswith('AFN6_') and o.type=='MESH'),key=lambda o:o.name):
  mesh=obj.data;mesh.calc_loop_triangles();edges=Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in mesh.polygons for i in range(len(p.vertices)));badnorm=0
  if obj['aevrynd_optical_component']=='Sclera':
   b=rig.data.bones[obj.vertex_groups[0].name];centre=b.head_local
   badnorm=sum(p.normal.dot(p.center-centre)<0 for p in mesh.polygons)
  else:badnorm=sum(p.normal.dot(Vector((0.,-1.,0.)))<=0 for p in mesh.polygons)
  parts.append({'name':obj.name,'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'boundaryEdges':sum(n==1 for n in edges.values()),'edgesOverTwoFaces':sum(n>2 for n in edges.values()),'nonFiniteVertices':sum(any(not math.isfinite(x) for x in v.co) for v in mesh.vertices),'wrongDirectionFaces':badnorm,'maximumWeightSumError':max(abs(sum(g.weight for g in v.groups)-1) for v in mesh.vertices),'materials':[m.name for m in mesh.materials]})
  if label=='b-balanced':
   pe=obj.evaluated_get(dg);pm=pe.to_mesh();visibility=Counter();faces=set();samples=[]
   for vi,vertex in enumerate(pm.vertices):
    p=pe.matrix_world@vertex.co;hit=tree.find_nearest(p);signed=(p-hit[0]).dot(hit[1].normalized())
    if signed>=0:continue
    h=hit[0];front=tree.ray_cast(Vector((h.x,-.4,h.z)),Vector((0.,1.,0.)),.5);kind='front-projected-lid' if front[0] is not None and abs(front[0].y-h.y)<.00008 else 'recessed-socket';visibility[kind]+=1;faces.add(control.find_nearest(h)[2])
    if len(samples)<6:samples.append({'eyeVertex':vi,'eyeWorld':list(p),'bodyNearest':list(h),'bodyNormal':list(hit[1]),'signedM':signed,'frontalClassification':kind})
   localization[obj.name]={'negativeVertexClassification':dict(visibility),'nearestNativeControlFaces':sorted(faces),'sampleContacts':samples};pe.to_mesh_clear()
 ev.to_mesh_clear()
 retained_bones=max(abs(rig.data.bones[name].matrix_local[i][j]-mat[i][j]) for name,mat in source_bones.items() for i in range(4) for j in range(4))
 result.append({'label':label,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'bodyControlMeshMatchesR0005':mesh_hash(body.data)==source_hash,'retainedRigRestMatrixMaximumError':retained_bones,'rigBones':len(rig.data.bones),'eyeObjects':len(parts),'eyeStatistics':parts,'neutralContactLocalization':localization,'packedImages':[{'name':i.name,'size':list(i.size),'packed':i.packed_file is not None} for i in bpy.data.images],'externalLibraries':[l.filepath for l in bpy.data.libraries],'factoryStartup':True,'enabledAddons':list(bpy.context.preferences.addons.keys())})
(E/'saved-eye-verification.json').write_text(json.dumps({'revision':'female-next-r0006','baselineControlMeshHash':source_hash,'results':result,'scope':'file integrity, native body preservation, optical topology and diagnostic localization only; no quality promotion'},indent=2)+'\n')
print(json.dumps([{'label':r['label'],'bodyPreserved':r['bodyControlMeshMatchesR0005'],'rigRestError':r['retainedRigRestMatrixMaximumError'],'eyeObjects':r['eyeObjects'],'badNormals':sum(p['wrongDirectionFaces'] for p in r['eyeStatistics']),'badVertices':sum(p['nonFiniteVertices'] for p in r['eyeStatistics']),'eyeTriangles':sum(p['triangles'] for p in r['eyeStatistics']),'packedImages':r['packedImages']} for r in result],indent=2))
