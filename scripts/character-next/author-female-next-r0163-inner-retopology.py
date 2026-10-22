"""Actual native wall remesh, one target, original boundary/source retained."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime,collections
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0163-remeshed-inner-lids';sp=importlib.util.spec_from_file_location('r163author',C/'scripts/character-next/build-female-next-r0161-contact-membrane-lids.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;m.E=E;h.E=E
b=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['source']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();reference=bpy.data.objects['AFN161_ORIGINAL_NATIVE_MARGIN_POSE_REFERENCE'];V,T=a.geometry(reference);z=np.load(E.parent/'r0161-contact-membrane-lids/actual-fixed-wall-source-map.npz');domain=set(map(int,z['oldDomainFaces']));ids=np.array(sorted(set(int(v) for fi in domain for v in reference.data.polygons[fi].vertices)),'i4');mapping={int(v):i for i,v in enumerate(ids)};reference.data.calc_loop_triangles();tri=[t for t in reference.data.loop_triangles if t.polygon_index in domain];F=np.array([[mapping[int(v)] for v in t.vertices] for t in tri],'i4');wall=m.meshob('AFN163_ACTUAL_RETETOPOLOGY_INNER_WALL',V[ids],F);bpy.ops.object.select_all(action='DESELECT');wall.hide_set(False);wall.select_set(True);bpy.context.view_layer.objects.active=wall;schema={p.identifier for p in bpy.ops.object.quadriflow_remesh.get_rna_type().properties};h.save('actual-native-retopology-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':b['startedUTC'],'actualSourceVertices':len(ids),'actualSourceTriangles':len(F),'operatorRNA':sorted(schema),'oneRequestedFaceTarget':1600,'actualPurpose':'Replace old Boolean slivers with new regular native topology, preserve boundary shape, then explicitly reconnect original shared rim IDs. Not a density sweep or repeated old cloth parameters.'});assert 'use_preserve_boundary' in schema and 'target_faces' in schema;kwargs={'target_faces':1600,'use_preserve_boundary':True}
for key,value in [('use_mesh_symmetry',False),('use_preserve_sharp',False),('smooth_normals',False),('seed',0)]:
 if key in schema:kwargs[key]=value
tick=time.time();result=bpy.ops.object.quadriflow_remesh(**kwargs);P=h.arr(wall.data.vertices,'co',len(wall.data.vertices),3);faces=[list(f.vertices) for f in wall.data.polygons];edges=collections.Counter(tuple(sorted((u,v))) for f in faces for u,v in zip(f,f[1:]+f[:1]));adj=collections.defaultdict(list)
for (u,v),count in edges.items():
 if count==1:adj[u].append(v);adj[v].append(u)
loops=[];remaining=set(adj)
if all(len(v)==2 for v in adj.values()):
 while remaining:
  start=min(remaining);loop=[start];prev=None;cur=start
  while True:
   nxt=next(v for v in adj[cur] if v!=prev)
   if nxt==start:break
   loop.append(nxt);prev,cur=cur,nxt
  loops.append(loop);remaining.difference_update(loop)
flat=np.array([i for f in faces for i in f],'i4');counts=np.array(list(map(len,faces)),'i4');np.savez_compressed(E/'authored-native-inner-retopology.npz',positions=P,faceIndices=flat,faceCounts=counts,originalWallVertexIds=ids,originalSourcePositions=V[ids]);h.save('authored-native-inner-retopology.json',{'operatorResult':sorted(result),'vertices':len(P),'faces':len(faces),'faceSizeHistogram':dict(collections.Counter(map(len,faces))),'boundaryLoops':loops,'boundaryLoopLengths':[len(x) for x in loops],'boundaryDegreeHistogram':dict(collections.Counter(map(len,adj.values()))),'nativeSeconds':time.time()-tick,'geometryAuthoringOnlyNotCompleteCharacterOrContactPass':True});print('R163_ACTUAL_NATIVE_INNER_RETOPOLOGY_AUTHORED',len(P),len(faces),[len(x) for x in loops],time.time()-tick,flush=True)
