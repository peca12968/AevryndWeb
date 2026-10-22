"""Independently reopen immutable B; qualify native edit scope, not full blink."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,collections
R=Path('D:/Download/Aevrynd');C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');M=C/'assets-source/aevrynd-character/female-next';E=C/'evidence/character-female-next/r0158-shared-native-skin'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=mod('r158verify',C/'scripts/character-next/build-female-next-r0158-shared-native-skin.py');a=h.a
c=mod('r158contact',R/'scripts/character-next/contact-female-next-r0138-ocular-surfaces.py');edge=mod('r158edge',R/'scripts/character-next/build-female-next-r0138-native-sockets.py')
def save(n,x):h.save(n,x)
def geom(ob):return a.geometry(ob)
def dependencies():
 libs=[];textures=[]
 for lib in bpy.data.libraries:
  p=Path(bpy.path.abspath(lib.filepath)).resolve();assert p.is_file();libs.append({'file':str(p),'sha256':a.a.sha(p)})
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert p.is_file();textures.append({'file':str(p),'sha256':a.a.sha(p)})
 assert len(libs)==1 and len(textures)==16
 assert libs[0]['sha256']=='6d14dcca0c0a3dc2a8be613d92377a663522dbb8d31a3f26ec894132723f1480'
 return {'libraries':libs,'textures':textures}
tick=time.time();b=json.loads((E/'b-build-summary.json').read_text());p=Path(b['output']);assert a.a.sha(p)==b['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;rig=bpy.data.objects[b['actualRig']];skin=bpy.data.objects[b['actualSkin']];source=bpy.data.objects[b['actualPoseSource']];names=a.FIXED+a.MOVING;ATTACH=a.FIXED[2:4];z=np.load(E/'explicit-shared-skin-lineage.npz');keep=z['retainedSourceVertices'];mapping=z['sourceToNative'];nativeBoundary=set(map(int,z['nativeBoundaryVertices']));s.frame_set(1);bpy.context.view_layer.update();rest={n:geom(bpy.data.objects[n])[0] for n in names};assert len(rest[skin.name])==170227 and len(skin.data.polygons)==187372
deps=dependencies();repair=json.loads((E/'material-and-data-preservation-repair.json').read_text());slots=[x.name if x else None for x in skin.data.materials];assert slots==repair['restoredOriginalMainMaterialSlots'];ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());old=ev.to_mesh();attrs=[]
for name in ['AFN113_NATIVE_COLOR_WEIGHT','AFN126_NECK_BLEND']:
 A=h.arr(old.attributes[name].data,'value',len(old.vertices));B=h.arr(skin.data.attributes[name].data,'value',len(skin.data.vertices));assert np.array_equal(A[keep],B);attrs.append({'name':name,'mappedValuesPersistExactly':True})
ev.to_mesh_clear()
# Source-identified edges, with actual native vertex identities, no tolerance.
loops=json.loads((R/'Evidence/character-female-next/r0157-outer-lid-retopology/actual-outer-lid-boundaries.json').read_text());boundaryMap=dict(zip(map(int,z['originalBoundaryVertices']),map(int,z['nativeBoundaryVertices'])));edges={tuple(sorted((boundaryMap[u],boundaryMap[v]))):[0,0] for row in loops['reports'] for loop in row['loops'] for u,v in zip(loop['originalVertexIds'],loop['originalVertexIds'][1:]+loop['originalVertexIds'][:1])}
for f in skin.data.polygons:
 ids=list(f.vertices)
 for u,v in zip(ids,ids[1:]+ids[:1]):
  key=tuple(sorted((u,v)))
  if key in edges:edges[key][0]+=1;edges[key][1]+=1 if u<v else -1
assert len(edges)==536 and all(x==[2,0] for x in edges.values());rows=[]
for frame in [1,9,11,24]:
 s.frame_set(frame);bpy.context.view_layer.update();V,T=geom(skin);SV,_=geom(source);assert len(V)==170227 and np.isfinite(V).all();error=float(np.linalg.norm(V-SV[keep],axis=1).max());assert error==0
 rows.append({'frame':frame,'blink':[float(rig[k]) for k in ['blink_L','blink_R']],'actualVertices':len(V),'actualTriangles':len(T),'actualPoseSourceMappingErrorM':error,'layerMovementMaximumM':{n:float(np.linalg.norm(geom(bpy.data.objects[n])[0]-rest[n],axis=1).max()) for n in names}})
assert max(rows[-1]['layerMovementMaximumM'].values())==0;s.frame_set(11);bpy.context.view_layer.update();baseline={n:geom(bpy.data.objects[n])[0] for n in [skin.name,*ATTACH]};edits=[]
for name in ATTACH:
 table=bpy.data.objects['AFN155_'+name+'_BLINK_ATTACHMENT'].data;N=len(table.vertices);ids=np.empty((N,3),'i4');bc=h.arr(table.attributes['AFN155_BC'].data,'vector',N,3)
 for k in range(3):ids[:,k]=h.arr(table.attributes['AFN155_V'+str(k)].data,'value',N,dtype='i4')
 candidates=[(row,k,int(ids[row,k])) for row in range(N) for k in range(3) if bc[row,k]>.001 and int(ids[row,k]) in nativeBoundary]
 usedBoundary=bool(candidates)
 if not candidates:candidates=[(row,k,int(ids[row,k])) for row in range(N) for k in range(3) if bc[row,k]>.001]
 assert candidates;row,k,vi=candidates[0];co=skin.data.vertices[vi].co.copy();skin.data.vertices[vi].co.y+=.0002;skin.data.update();skin.update_tag(refresh={'DATA'});bpy.context.view_layer.update();moves={n:float(np.linalg.norm(geom(bpy.data.objects[n])[0]-baseline[n],axis=1).max()) for n in baseline};skin.data.vertices[vi].co=co;skin.data.update();skin.update_tag(refresh={'DATA'});bpy.context.view_layer.update();restore={n:float(np.linalg.norm(geom(bpy.data.objects[n])[0]-baseline[n],axis=1).max()) for n in baseline};assert abs(moves[skin.name]-.0002)<1e-7 and moves[name]>1e-7 and max(restore.values())==0
 edits.append({'targetActualLayer':name,'vertex':vi,'isActualSharedBoundaryVertex':usedBoundary,'attachmentRow':row,'barycentricWeight':float(bc[row,k]),'rawMeshPositionDeltaM':.0002,'actualDisplayedMovementM':moves,'restorationM':restore,'noSourceSavedOrControlFieldEdited':True})
save('actual-native-mesh-edit-and-restoration.json',{'actualSkin':skin.name,'actualMesh':skin.data.name,'actualSharedBoundaryEdges536EachTwoOppositeFaces':True,'edits':edits,'scope':'Native raw-position editing and selected actual attachment response only; not complete blink/finite contact/runtime acceptance.'})
# Original local failure scope stays explicit: eight wall triangles, full eyes.
V,T=geom(skin);ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.to_mesh();d.calc_loop_triangles();poly=h.arr(d.loop_triangles,'polygon_index',len(d.loop_triangles),dtype='i4');wall=187115;assert len(d.polygons[wall].vertices)==10;selected=np.flatnonzero(poly==wall);ev.to_mesh_clear();assert len(selected)==8;cases=[]
for name in a.MOVING:
 W,F=geom(bpy.data.objects[name]);q=c.query(V[T[selected]],W[F],V[T[selected]].min(1),V[T[selected]].max(1));pairs=q['properCrossings'];witness=[]
 for si,ei in pairs[:2]:
  hits=edge.witness(V[T[selected[si]]],W[F[ei]]);assert len(hits)>=2;witness.append({'actualSkinTriangle':int(selected[si]),'eyeTriangle':int(ei),'finiteEdgeFaceWitnesses':hits})
 cases.append({'object':name,'testedActualEyeTriangles':len(F),'properCrossingPairs':len(pairs),'firstIndependentWitnesses':witness})
save('retained-original-wall-only-contact.json',{'frame':11,'actualOutputPolygon':wall,'testedActualOutputSkinTriangles':len(selected),'cases':cases,'localScopeOnly':True,'numericEpsilonM':1e-12,'wholeSkinFiniteSelfContinuousNotAccepted':True,'globalSignedMinimumM':None})
s.frame_set(1);bpy.context.view_layer.update();assert all(np.array_equal(geom(bpy.data.objects[n])[0],rest[n]) for n in names);assert a.a.sha(p)==b['sha256'];save('independent-native-source-readback.json',{'source':str(p),'sha256':b['sha256'],'actualNativeVertices':170227,'allOriginalPolygonsRetained':187372,'sharedBoundaryVertices':536,'sharedBoundaryEdgesEachTwoOppositeFaces':True,'effectiveMaterialSlotsPersisted':slots,'mappedShaderAttributes':attrs,'actualBlinkPoses':rows,'allSevenNeutralRestorationM':0,'actualRawPositionEditAndSelectedAttachmentRestoration':True,'dependencies':deps,'fullAppearanceBlinkContactRuntimeNotAccepted':True,'elapsedSeconds':time.time()-tick})
# Engine junction must independently resolve the same source and dependencies.
bpy.ops.wm.open_mainfile(filepath=b['engineAlias']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();alias=dependencies();assert a.a.sha(Path(b['engineAlias']))==b['sha256'];assert [x.name if x else None for x in bpy.data.objects[b['actualSkin']].data.materials]==slots;assert np.array_equal(geom(bpy.data.objects[b['actualSkin']])[0],rest[skin.name]);assert sorted(x['sha256'] for x in alias['textures'])==sorted(x['sha256'] for x in deps['textures']);save('independent-engine-alias-readback.json',{'engineAlias':b['engineAlias'],'sourceSha256':b['sha256'],'sameActualNeutralSkin':True,'sameEffectiveMaterials':True,'dependencies':alias,'filesNotModified':True});print('R158_INDEPENDENT_NATIVE_EDIT_RESTORE_SHARED_TOPOLOGY_MATERIALS_ALIAS_LOCAL_CONTACT_DONE',time.time()-tick,flush=True)
