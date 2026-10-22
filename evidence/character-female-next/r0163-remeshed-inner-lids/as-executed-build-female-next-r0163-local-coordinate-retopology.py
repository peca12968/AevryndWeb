"""Original163 continuation: orient native input, retopologize once, exact rim.
No new round/clock, numerical sweep or unchanged-cavity rebake. Native cloth
authors discrete engineering correctives only; final displayed contacts unproven.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,importlib.util,time,datetime,collections
from mathutils.bvhtree import BVHTree
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0163-remeshed-inner-lids';OUT=C/'assets-source/aevrynd-character/female-next/r0163-source/aevrynd-female-next-r0163-a-remeshed-inner-lids.blend';K=100.
sp=importlib.util.spec_from_file_location('r163base',C/'scripts/character-next/build-female-next-r0161-contact-membrane-lids.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;g=m.g;m.E=E;h.E=E
def loops(F):
 edges=collections.Counter(tuple(sorted((u,v))) for f in F for u,v in zip(f,f[1:]+f[:1]));adj=collections.defaultdict(list)
 for (u,v),count in edges.items():
  if count==1:adj[u].append(v);adj[v].append(u)
 assert all(len(v)==2 for v in adj.values());remaining=set(adj);out=[]
 while remaining:
  start=min(remaining);chain=[start];prev=None;cur=start
  while True:
   nxt=next(v for v in adj[cur] if v!=prev)
   if nxt==start:break
   chain.append(nxt);prev,cur=cur,nxt
  out.append(chain);remaining.difference_update(chain)
 return out,edges
def main():
 tick=time.time();before=json.loads((E/'before.json').read_text());assert not OUT.exists();assert a.a.sha(Path(before['source']))==before['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=before['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];reference=bpy.data.objects['AFN161_ORIGINAL_NATIVE_MARGIN_POSE_REFERENCE'];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];V,_=a.geometry(reference);old=skin.data;z=np.load(E.parent/'r0161-contact-membrane-lids/actual-fixed-wall-source-map.npz');domain=set(map(int,z['oldDomainFaces']));oldWall=set(map(int,z['newWallPolygons']));q=np.load(E/'authored-native-inner-retopology.npz');P=q['positions'].astype('f8');counts=q['faceCounts'];flat=q['faceIndices'];F=[];off=0
 for count in counts:F.append(flat[off:off+count].tolist());off+=count
 originalIds=q['originalWallVertexIds'];originalLoops,edges=loops(F);assert max(edges.values())<=2,'Nonmanifold edge: no face removal or automatic retry';wall=m.meshob('AFN163_ACTUAL_ORIENTED_RETOPOLOGY_WALL',P,F);bm=bmesh.new();bm.from_mesh(wall.data);beforeNormals=[tuple(f.normal) for f in bm.faces];bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(wall.data);bm.free();wall.data.update();oriented=[list(f.vertices) for f in wall.data.polygons];directed=collections.defaultdict(list)
 for f in oriented:
  for u,v in zip(f,f[1:]+f[:1]):directed[tuple(sorted((u,v)))].append((u,v))
 inconsistent=sum(len(x)==2 and x[0]==x[1] for x in directed.values());assert inconsistent==0
 oldF=np.array(F,'i4');rawDirected=collections.defaultdict(list)
 for f in F:
  for u,v in zip(f,f[1:]+f[:1]):rawDirected[tuple(sorted((u,v)))].append((u,v))
 oldInconsistent=sum(len(x)==2 and x[0]==x[1] for x in rawDirected.values())
 m.save('direct-local-coordinate-retopology-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalTiming':before,'originalOperatorWasCancelled':True,'originalSuccessMarkerNotTrusted':True,'originalSharedEdgesWithSameDirectedUse':oldInconsistent,'afterActualNativeFaceOrientationRepair':inconsistent,'inputMaximumEdgeIncidence':max(edges.values()),'oneChangedInputCoordinateRetopologyAttempt':True,'priorWindingHypothesisDisproved':True,'changedPremise':'Original topology has consistent winding and manifold links; original cancellation cause remains unresolved. Recenter and scale native operator input100 to condition submicron edges, then invert exact coordinate transform. No anatomical push, density sweep or assumption this proves the cause. Support time exceeded original deadline; no extension or reset.'})
 origin=P.mean(0);wall.data.vertices.foreach_set('co',((P-origin)*K).astype('f4').ravel());wall.data.update()
 bpy.ops.object.select_all(action='DESELECT');wall.hide_set(False);wall.select_set(True);bpy.context.view_layer.objects.active=wall;result=bpy.ops.object.quadriflow_remesh(target_faces=1600,use_preserve_boundary=True,use_mesh_symmetry=False,use_preserve_sharp=False,seed=0)
 m.save('actual-local-coordinate-retopology-operator-return.json',{'result':sorted(result),'originalCancelledAttemptRetained':True,'sourceFaces':len(F),'outputFaces':len(wall.data.polygons)})
 assert result=={'FINISHED'},'No repeat after corrected input failure'
 P=h.arr(wall.data.vertices,'co',len(wall.data.vertices),3).astype('f8')/K+origin;F=[list(f.vertices) for f in wall.data.polygons];newLoops,newEdges=loops(F);assert len(newLoops)==len(originalLoops)==2
 # Reconnect original anatomical boundary IDs: ordered unique anchors and
 # explicit insertion of every original rim point, never a distance weld.
 mapping={};insert={};boundaryRecords=[]
 for newLoop in newLoops:
  center=P[newLoop].mean(0);oldLoop=min(originalLoops,key=lambda l:np.linalg.norm(V[originalIds[l]].mean(0)-center));oldGlobal=originalIds[oldLoop].tolist();oldP=V[oldGlobal];n=len(oldLoop);assert len(newLoop)<=n,'Boundary subdivision exceeds original source boundary, no collapse fallback'
  dist=np.linalg.norm(P[newLoop,None,:]-oldP[None,:,:],axis=2);anchor=np.argmin(dist,axis=1).tolist()
  assert len(set(anchor))==len(anchor),'Retopology has ambiguous anatomical boundary anchors; no nearest weld'
  forward=sum((anchor[(i+1)%len(anchor)]-anchor[i])%n for i in range(len(anchor)))
  backward=sum((anchor[i]-anchor[(i+1)%len(anchor)])%n for i in range(len(anchor)))
  direction=1 if forward==n else -1;assert (forward if direction==1 else backward)==n
  for vi,ai in zip(newLoop,anchor):mapping[vi]=int(oldGlobal[ai]);P[vi]=oldP[ai]
  for i,u in enumerate(newLoop):
   v=newLoop[(i+1)%len(newLoop)];ai=anchor[i];aj=anchor[(i+1)%len(newLoop)];chain=[];x=(ai+direction)%n
   while x!=aj:chain.append(int(oldGlobal[x]));x=(x+direction)%n
   insert[(u,v)]=chain;insert[(v,u)]=chain[::-1]
  boundaryRecords.append({'retopologyBoundary':len(newLoop),'originalTrueSharedBoundary':n,'allOriginalPointsReinserted':True,'maximumBoundaryAnchorCorrectionM':float(dist[np.arange(len(anchor)),anchor].max())})
 newV=V.tolist();interior=[]
 for vi,p in enumerate(P):
  if vi not in mapping:mapping[vi]=len(newV);newV.append(p.tolist());interior.append(vi)
 newWall=[]
 for face in F:
  out=[]
  for u,v in zip(face,face[1:]+face[:1]):out.append(mapping[u]);out.extend(insert.get((u,v),[]))
  newWall.append(out)
 # Orient against retained source outer edge uses, then fixed native triangles.
 keep=[f for f in old.polygons if f.index not in oldWall];outerDirected={tuple(sorted((u,v))):(u,v) for f in keep for u,v in zip(list(f.vertices),list(f.vertices)[1:]+list(f.vertices)[:1])};tissue=m.meshob('AFN163_ACTUAL_SHARED_RIM_NEW_WALL',np.array(newV),newWall);bm=bmesh.new();bm.from_mesh(tissue.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.faces.ensure_lookup_table();seen=set()
 for seed in bm.faces:
  if seed in seen:continue
  component={seed};queue=[seed]
  while queue:
   f=queue.pop()
   for ed in f.edges:
    for nb in ed.link_faces:
     if nb not in component:component.add(nb);queue.append(nb)
  seen.update(component);votes=[]
  for f in component:
   for loop in f.loops:
    u=loop.vert.index;v=loop.link_loop_next.vert.index;edge=tuple(sorted((u,v)))
    if edge in outerDirected:votes.append((u,v)==outerDirected[edge])
  if votes and sum(votes)>len(votes)/2:bmesh.ops.reverse_faces(bm,faces=list(component))
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(tissue.data);bm.free();wallGlobal=np.array([list(f.vertices) for f in tissue.data.polygons],'i4');Nold=len(V);newV=np.array(newV,'f4');used=np.array(sorted(set(wallGlobal.ravel().tolist())),'i4');loc={int(v):i for i,v in enumerate(used)};localF=np.array([[loc[int(v)] for v in f] for f in wallGlobal],'i4');boundaryGlobal=set(mapping[v] for loop in newLoops for v in loop);pins=np.array([int(v in boundaryGlobal) for v in used],'i4');assert len(boundaryGlobal)==366
 # New local native Skin; retained polygons/UV/custom normals are exact.
 faces=[list(f.vertices) for f in keep]+wallGlobal.tolist();mesh=bpy.data.meshes.new('AFN163_NATIVE_SKIN_RETOPOLOGIZED_INNER_LIDS_EXACT_RIM');mesh.from_pydata(newV.tolist(),[],faces);mesh.update()
 for material in old.materials:mesh.materials.append(material if material else next(x for x in old.materials if x))
 for i,material in enumerate(old.materials):
  if material is None:mesh.materials[i]=None
 for i,f in enumerate(mesh.polygons):f.material_index=old.polygons[keep[i].index].material_index if i<len(keep) else 0;f.use_smooth=old.polygons[keep[i].index].use_smooth if i<len(keep) else True
 # Actual old wall triangles define interpolation, not copied third-party data.
 reference.data.calc_loop_triangles();ot=[t for t in reference.data.loop_triangles if t.polygon_index in domain];oldTriangles=np.array([list(t.vertices) for t in ot],'i4');tree=BVHTree.FromPolygons([Vector(x) for x in V],oldTriangles.tolist(),all_triangles=True);nearest=[];bary=[]
 for p in newV[Nold:]:
  hit,normal,ti,d=tree.find_nearest(Vector(p));A=V[oldTriangles[ti]];u=A[1]-A[0];v=A[2]-A[0];q=np.array(hit)-A[0];uv=np.linalg.lstsq(np.column_stack((u,v)),q,rcond=None)[0];nearest.append(ti);bary.append([1-uv.sum(),*uv])
 nearest=np.array(nearest,'i4');bary=np.array(bary,'f4');loopOrder=np.array([li for f in keep for li in range(f.loop_start,f.loop_start+f.loop_total)],'i4');newLoopVert=np.array([v for f in wallGlobal for v in f],'i4')
 for uv in old.uv_layers:
  values=h.arr(uv.data,'uv',len(uv.data),2);ruv=h.arr(reference.data.uv_layers[uv.name].data,'uv',len(reference.data.loops),2);pointUV=np.zeros((len(newV),2),'f4');assigned=np.zeros(Nold,bool)
  for tri in ot:
   for vi,li in zip(tri.vertices,tri.loops):pointUV[vi]=ruv[li];assigned[vi]=True
  oldUV=np.array([[ruv[li] for li in tri.loops] for tri in ot]);pointUV[Nold:]=(oldUV[nearest]*bary[:,:,None]).sum(1);dst=mesh.uv_layers.new(name=uv.name);dst.data.foreach_set('uv',np.concatenate((values[loopOrder],pointUV[newLoopVert])).ravel());dst.active_render=uv.active_render;dst.active_clone=uv.active_clone
 mesh.uv_layers.active_index=old.uv_layers.active_index
 for name in ['AFN113_NATIVE_COLOR_WEIGHT','AFN126_NECK_BLEND']:
  values=h.arr(old.attributes[name].data,'value',Nold);extra=(values[oldTriangles[nearest]]*bary).sum(1);m.attr(mesh,name,np.concatenate((values,extra)))
 parents=h.arr(old.attributes['AFN117_NATIVE_PARENT_FACE'].data,'value',len(old.polygons),dtype='i4');m.attr(mesh,'AFN117_NATIVE_PARENT_FACE',np.concatenate((parents[[f.index for f in keep]],np.full(len(wallGlobal),-1,'i4'))),'FACE');norm=np.concatenate((h.arr(old.corner_normals,'vector',len(old.loops),3)[loopOrder],np.zeros((len(newLoopVert),3),'f4')));mesh.normals_split_custom_set(norm.tolist());wi=np.zeros(len(newV),'i4');wi[used]=np.arange(len(used));inside=np.zeros(len(newV),'i4');inside[used[pins==0]]=1;m.attr(mesh,'AFN161_WALL_INDEX',wi);m.attr(mesh,'AFN161_WALL_INTERIOR',inside);m.attr(mesh,'AFN161_EDIT_REST',newV)
 membrane=m.meshob('AFN163_LAB_NEW_TOPOLOGY_EXACT_RIM_MEMBRANE',newV[used]*K,localF);m.attr(membrane.data,'AFN161_PIN',pins);sourceIds=np.minimum(used,Nold-1).astype('i4');m.attr(membrane.data,'AFN161_SOURCE_VERTEX',sourceIds);m.pin_graph(membrane,reference);ng=membrane.modifiers[0].node_group;setpos=next(n for n in ng.nodes if n.bl_idname=='GeometryNodeSetPosition');socket=setpos.inputs['Position'].links[0].from_socket;scale=ng.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=K;ng.links.new(socket,scale.inputs[0]);ng.links.new(scale.outputs[0],setpos.inputs['Position']);vg=membrane.vertex_groups.new(name='AFN163_ORIGINAL_SHARED_RIM_PINS');vg.add(np.flatnonzero(pins).tolist(),1.,'REPLACE');cloth=membrane.modifiers.new('AFN163_NATIVE_NEW_TOPOLOGY_CONTACT_AUTHORING','CLOTH');cs=cloth.settings;cc=cloth.collision_settings
 for key,value in [('quality',12),('mass',.001),('tension_stiffness',30.),('compression_stiffness',30.),('shear_stiffness',15.),('bending_stiffness',1.),('vertex_group_mass',vg.name),('use_dynamic_mesh',False)]:setattr(cs,key,value)
 cs.effector_weights.gravity=0.;cc.use_collision=True;cc.collision_quality=8;cc.distance_min=.0002*K;cc.use_self_collision=True;cc.self_distance_min=.00015*K;cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=24;outer=bpy.data.objects['AFN162_LAB_ACTUAL_MOVING_OUTER_SKIN'];outer.hide_set(False);steps=[];stats=[];raw=[]
 for frame in range(1,25):
  s.frame_set(frame);bpy.context.view_layer.update();W,_=a.geometry(membrane);W/=K;assert np.isfinite(W).all();target=a.geometry(reference)[0];error=float(np.linalg.norm(W[pins>0]-target[used[pins>0]],axis=1).max());raw.append(W.astype('f4'));W[pins>0]=target[used[pins>0]];steps.append(W.astype('f4'));stats.append({'frame':frame,'rawSolverBoundaryErrorM':error,'displayedSharedBoundaryAuthoredExactly':True,'maxDisplacementM':float(np.linalg.norm(W-newV[used],axis=1).max()),'blink':[float(rig[k]) for k in ['blink_L','blink_R']]});m.save('actual-remeshed-wall-authoring-progress.json',stats);print('R163_NEW_TOPOLOGY_FRAME',frame,error,flush=True)
 cloth.show_render=cloth.show_viewport=False;membrane.hide_set(True);outer.hide_set(True);baked=m.meshob('AFN163_ACTUAL_RETOPOLOGY_SHARED_RIM_CORRECTIVES',steps[0],localF);baked.shape_key_add(name='Basis')
 for i in range(1,24):
  key=baked.shape_key_add(name='AFN163_RETOPOLOGY_FRAME_%02d'%(i+1));key.data.foreach_set('co',steps[i].ravel())
  for frame,value in [(i,0.),(i+1,1.),(i+2,0.)]:key.value=value;key.keyframe_insert(data_path='value',frame=frame)
 for layer in baked.data.shape_keys.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 baked.hide_set(True);skin.modifiers.clear();skin.data=mesh;m.skin_graph(skin,reference,baked);s.frame_set(1);bpy.context.view_layer.update();np.savez_compressed(E/'actual-remeshed-wall-source-map.npz',globalVertexIds=used,wallTriangles=wallGlobal,newWallPolygons=np.arange(len(keep),len(faces),dtype='i4'),originalSourceVertexCount=Nold,retainedOriginalPolygons=np.array([f.index for f in keep],'i4'),boundaryVertexIds=np.array(sorted(boundaryGlobal),'i4'));np.savez_compressed(E/'actual-remeshed-wall-states.npz',positions=np.array(steps),rawSolverPositions=np.array(raw),frames=np.arange(1,25));m.save('actual-new-topology-construction.json',{'boundary':boundaryRecords,'sharedOriginalBoundaryIds':366,'oldWallFacesRemoved':len(oldWall),'newFixedWallTriangles':len(wallGlobal),'newWallVertices':len(used),'newSkinVertices':len(mesh.vertices),'originalRetainedOuterPolygons':len(keep),'newNativeSkinMeshLocalEditable':True,'sameReferenceAndRootAngularFibreConstruction':True,'originalUnusedInteriorVerticesRetainedButNotRendered':int(len(originalIds)-366),'actualSolverPinMaxErrorM':max(x['rawSolverBoundaryErrorM'] for x in stats),'exactDisplayBoundaryIsAuthoredOverrideNotSolverProof':True,'engineeringApproximationNotPhysiologicalPhysics':True,'finiteSelfContinuousAndCompleteOperationUnaccepted':True});assert a.a.sha(Path(before['source']))==before['sourceSha256'];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);m.save('a-build-summary.json',{'source':before['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0163-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualPoseSource':reference.name,'actualWallCorrectives':baked.name,'unaccepted':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<before['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
 for frame,view,tag in [(11,'face','a-remeshed-lids-closed'),(11,'body-face','a-remeshed-lids-closed'),(1,'face','a-remeshed-lids-neutral'),(9,'face','a-remeshed-lids-half')]:
  s.frame_set(frame);bpy.context.view_layer.update();_=a.geometry(skin)
  for name in a.FIXED[2:4]:_=a.geometry(bpy.data.objects[name])
  ctl=a.b.u.v.image(tag,view);ctl.update(frame=frame,blink=[float(rig[k]) for k in ['blink_L','blink_R']]);views.append(ctl);m.save('actual-remeshed-lids-preview-controls.json',views)
 s.frame_set(1);bpy.context.view_layer.update();print('R163_COMPLETE_RETOPOLOGY_HEAD_BODY_NEUTRAL_HALF_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
