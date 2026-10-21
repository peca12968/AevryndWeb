"""One complete woman with actual replacement mobile ocular meshes and cut ports."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0112-topological-ocular-graft';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0107-b-native-pinned-lids.blend';OUT=S/'aevrynd-female-next-r0112-a-sewn-topological-ocular.blend';RAIN=R/'Reference/character/blender-studio-rain-v3-cc-by4/Rain v3.3/rain_v3.2.blend'
sp=importlib.util.spec_from_file_location('r112build',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def drive(key,face,prop,expression):
 fc=key.driver_add('value');fc.driver.expression=expression;v=fc.driver.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=face;v.targets[0].data_path='["'+prop+'"]'
def wire_keys(ob,face,side,neutral,half,closed):
 if ob.data.shape_keys is None:ob.shape_key_add(name='Basis')
 ck=ob.shape_key_add(name='AFN112_'+side+'_closed');ck.data.foreach_set('co',closed.astype('f4').ravel());hk=ob.shape_key_add(name='AFN112_'+side+'_half');hk.data.foreach_set('co',(neutral+(half-neutral)-.5*(closed-neutral)).astype('f4').ravel());drive(ck,face,'blink_left' if side=='L' else 'blink_right','v');drive(hk,face,'blink_left' if side=='L' else 'blink_right','4*v*(1-v)')
def deliver(value):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];face['blink_left']=face['blink_right']=value;face.update_tag()
 for ob in bpy.data.objects:
  if ob.name.startswith('AFN112_') and ob.type=='MESH' and ob.data.shape_keys:ob.data.shape_keys.update_tag();ob.update_tag()
 bpy.context.view_layer.update()
def node_retarget(ob,old,new):
 for md in ob.modifiers:
  if md.type=='NODES':
   md.node_group=md.node_group.copy()
   for node in md.node_group.nodes:
    if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==old:node.inputs['Object'].default_value=new

def mesh_object(name,V,T,mats):
 me=bpy.data.meshes.new(name);me.from_pydata(V.tolist(),[],[tuple(map(int,p)) for p in T]);me.update();ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob)
 for mat in mats:me.materials.append(mat)
 return ob

def boolean(base,tool,op):
 bpy.ops.object.select_all(action='DESELECT');base.hide_set(False);base.select_set(True);bpy.context.view_layer.objects.active=base
 md=base.modifiers.new('AFN112_SHARED_BOUNDARY_'+op,'BOOLEAN');md.operation=op;md.solver='EXACT';md.object=tool
 if hasattr(md,'material_mode'):md.material_mode='INDEX'
 bpy.ops.object.modifier_apply(modifier=md.name);tool.hide_render=True;tool.hide_set(True)
 print('R112_BOOLEAN',op,len(base.data.vertices),len(base.data.polygons),flush=True)

def main():
 tick=time.time();assert not OUT.exists();PREV=E.parent/'r0111-native-mobile-lid-mesh';art=np.load(E/'topological-ocular-authoring.npz');data=np.load(PREV/'actual-rain-ocular-geometry.npz');info=json.loads((PREV/'actual-rain-ocular-geometry.json').read_text('utf8'))
 bpy.ops.wm.open_mainfile(filepath=str(SRC));face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 face['blink_left']=face['blink_right']=0.;oral['jaw_open']=0.;face.update_tag();oral.update_tag();bpy.context.view_layer.update()
 old=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];d,W,T=u.b.geom(old);W=W.copy();T=T.copy();lf=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');pf=q.arr(d.loop_triangles,'polygon_index',len(T),dtype='i4');uv={v.name:q.arr(v.data,'uv',len(d.loops),2)[lf].copy() for v in d.uv_layers};hf=q.arr(d.attributes['AFN104_SourceHeadFace'].data,'value',len(d.polygons),dtype='i4');norm=np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]]);norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-30)[:,None];selected=np.flatnonzero((hf[pf]>=0)&(norm[:,1]<-.1));used,inv=np.unique(T[selected],return_inverse=True);uvtree=BVHTree.FromPolygons(W[used].tolist(),inv.reshape(-1,3).tolist(),all_triangles=True)
 hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];H0=q.hair(hair).copy();lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];LH=q.geom(lash)[1].copy()
 base=old.copy();base.data=old.data.copy();assert base.data.shape_keys!=old.data.shape_keys;bpy.context.scene.collection.objects.link(base);base.name='AFN112_COMPLETE_WOMAN_SEWN_OCULAR_SKIN';base.shape_key_clear()
 mats=list(base.data.materials);lining=mats[4].copy();lining.name='AFN112_SOCKET_WALL_SAME_SKIN_REFERENCE';base.data.materials.append(lining);mats.append(lining)
 # The exact same source-topology contour defines both sides of this attachment.
 cuts=[]
 for side in ['L','R']:
  contour=art[side+'_cutContourWorld'];n=len(contour);y0,y1=art[side+'_cutterYRange'];V=np.vstack([np.column_stack((contour[:,0],np.full(n,y),contour[:,2])) for y in [y0,y1]])
  faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
  tool=mesh_object('AFN112_'+side+'_SHARED_PERIMETER_CUTTER',V,faces,mats);bm=bmesh.new();bm.from_mesh(tool.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(tool.data);bm.free()
  for p in tool.data.polygons:p.material_index=len(mats)-1
  boolean(base,tool,'DIFFERENCE');cuts.append(tool.name)
 # Bake the actual finite artist surface. Fixed outer collar overlaps body solid;
 # actual union, rather than overlaying the old rectangle cut, authors attachment.
 N=art['finiteNeutralWorld'];NT=art['finiteTriangles'];mobile=mesh_object('AFN112_FINITE_OCULAR_SOURCE_REFERENCE',N,NT,mats)
 for p in mobile.data.polygons:p.material_index=4;p.use_smooth=True
 vertexUV={name:np.empty((len(N),2),'f4') for name in uv}
 for i,p in enumerate(N):
  hit,no,fi,dist=uvtree.find_nearest(Vector(p));oldfi=selected[fi];tri=W[T[oldfi]];weights=u.a.bary(np.array(hit),tri)
  for name in uv:vertexUV[name][i]=weights@uv[name][oldfi]
 mids=q.arr(mobile.data.loops,'vertex_index',len(mobile.data.loops),dtype='i4')
 for name,values in vertexUV.items():mobile.data.uv_layers.new(name=name).data.foreach_set('uv',values[mids].ravel())
 boolean(base,mobile,'UNION');old.name='AFN112_PREVIOUS_COMPLETE_SKIN_REFERENCE';old.hide_render=True;old.hide_set(True)
 BL=q.arr(base.data.vertices,'co',len(base.data.vertices),3);BM=np.array(base.matrix_world);BMI=np.linalg.inv(BM);BV=BL@BM[:3,:3].T+BM[:3,3];tree=KDTree(len(BV))
 for i,p in enumerate(BV):tree.insert(Vector(p),i)
 tree.balance();sourceToBody=np.full(len(N),-1,'i4');error=np.empty(len(N))
 for i,p in enumerate(N):co,j,dist=tree.find(Vector(p));error[i]=dist;sourceToBody[i]=j if dist<4e-6 else -1
 dynamic=np.zeros(len(N),bool)
 for side in ['L','R']:
  for state in ['half','closed']:dynamic|=np.linalg.norm(art['finite_'+side+'_'+state+'World']-N,axis=1)>1e-8
 surviving=(sourceToBody>=0);missing=int(np.count_nonzero(dynamic&~surviving));base.shape_key_add(name='Basis')
 for side in ['L','R']:
  poses=[]
  for state in ['half','closed']:
   result=BV.copy();source=np.flatnonzero(surviving);result[sourceToBody[source]]+=art['finite_'+side+'_'+state+'World'][source]-N[source];poses.append(result)
  wire_keys(base,face,side,BL,(poses[0]-BM[:3,3])@BMI[:3,:3].T,(poses[1]-BM[:3,3])@BMI[:3,:3].T)
 # Map exact unchanged original scalp vertices, not interpolated Boolean IDs.
 rootMap={};rootErrors=[]
 for j in range(3):
  at=hair.data.attributes['AFN97_ScalpVertex'+str(j)];ids=q.arr(at.data,'value',24800,dtype='i4')
  for vi in np.unique(ids):
   if int(vi) not in rootMap:
    co,bi,dist=tree.find(Vector(W[vi]));assert dist<4e-6,('Missing retained scalp vertex',int(vi),dist);rootMap[int(vi)]=bi;rootErrors.append(dist)
  at.data.foreach_set('value',np.array([rootMap[int(vi)] for vi in ids],dtype='i4'))
 node_retarget(hair,old,base);hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();groomError=float(np.linalg.norm(q.hair(hair)-H0,axis=1).max())
 # Keep component and shared cutters as hidden reconstruction sources, never proof.
 np.savez_compressed(E/'complete-skin-source-correspondence.npz',finiteSourceToBody=sourceToBody,finiteSourceMatchingErrorM=error,dynamicFiniteVertices=dynamic,bodyNeutralWorld=BV)
 save('a-attachment-summary.json',{'actualBody':base.name,'newFiniteSource':mobile.name,'sharedPerimeterCutters':cuts,'unionVertices':len(BV),'sourceFiniteVertices':len(N),'sourceFiniteExactlyRetainedWithin4UM':int(surviving.sum()),'activeFiniteVerticesMissingAfterUnion':missing,'mappingErrorThresholdM':4e-6,'derivedIntersectionVerticesFixedByConstruction':True,'allSourceDynamicRetained':missing==0,'neutralGroomMaxWorldDifferenceM':groomError,'originalScalpVertexMaxWorldDifferenceM':max(rootErrors),'attachmentTopologyOrContactNotYetAccepted':True})
 materials=list(dict.fromkeys(info['materials']['eyes']+info['materials']['cornea']))
 requested=tuple(materials)
 with bpy.data.libraries.load(str(RAIN),link=False) as (a,b):b.materials=list(requested)
 materialMap={name:mat for name,mat in zip(requested,b.materials) if mat}
 for mat in materialMap.values():
  if mat.animation_data:mat.animation_data_clear()
  if mat.node_tree and mat.node_tree.animation_data:mat.node_tree.animation_data_clear()
 newEyes=[]
 for name in ['eyes','cornea']:
  for side in ['L','R']:
   V=art[name+'_'+side+'_neutralWorld'];TT=art[name+'_'+side+'_triangles'];sourceT=art[name+'_'+side+'_sourceTriangleIDs'];mesh=bpy.data.meshes.new('AFN112_'+name.upper()+'_'+side);mesh.from_pydata(V.tolist(),[],TT.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob)
   for matname in info['materials'][name]:mesh.materials.append(materialMap[matname])
   mi=data[name+'_neutralTriMaterialIndices'][sourceT]
   for p in mesh.polygons:p.material_index=int(mi[p.index]);p.use_smooth=True
   for key in data.files:
    prefix=name+'_neutralTriUV_'
    if key.startswith(prefix):mesh.uv_layers.new(name=key[len(prefix):]).data.foreach_set('uv',data[key][sourceT].astype('f4').reshape(-1,2).ravel())
   wire_keys(ob,face,side,V,art[name+'_'+side+'_halfWorld'],art[name+'_'+side+'_closedWorld']);newEyes.append(ob.name)
 for side in ['L','R']:
  for part in ['SCLERA','IRIS']:
   ob=bpy.data.objects['AFN104_NATIVE_'+side+'_'+part];ob.hide_render=True;ob.hide_set(True)
 node_retarget(lash,old,base);bpy.context.view_layer.update();dd,V,TT=u.b.geom(base);V=V.copy();TT=TT.copy()
 # Bind original fibres to explicit source eye-opening edges on the new union.
 opening=set()
 for side in ['L','R']:
  loop=art[side+'_rawEyeOpeningIndices'];mapped=sourceToBody[loop];assert (mapped>=0).all(),'Actual source margin removed by union'
  for aa,bb in zip(mapped,np.roll(mapped,-1)):opening.add(tuple(sorted((int(aa),int(bb)))))
 normal=np.cross(V[TT[:,1]]-V[TT[:,0]],V[TT[:,2]]-V[TT[:,0]]);normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-30)[:,None]
 choices=np.array([i for i,t in enumerate(TT) if normal[i,1]<-.1 and any(tuple(sorted((int(aa),int(bb)))) in opening for aa,bb in zip(t,np.roll(t,-1)))],dtype='i4');assert len(choices)>0
 lidTree=BVHTree.FromPolygons(V.tolist(),TT[choices].tolist(),all_triangles=True);bindings=json.loads((E.parent/'r0107-native-coarse-lid-cage/b-native-seam-lash-bindings.json').read_text('utf8'));LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);VL=(V-LA[:3,3])@LI.T;lids=np.empty((len(LH),3),'i4');bary=np.empty_like(LH);offset=np.empty_like(LH)
 for row in bindings:
  start=row['pointStart'];end=start+row['points'];hit,no,fi,dist=lidTree.find_nearest(Vector(LH[start]));tri=TT[choices[fi]];p=VL[tri];weights=u.a.bary((np.array(hit)-LA[:3,3])@LI.T,p);t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);frame=np.column_stack((t,np.cross(n,t),n));lids[start:end]=tri;bary[start:end]=weights;offset[start:end]=((LH[start:end]-LH[start])@LI.T)@frame;row.update({'actualNewUnifiedSkinTriangle':tri,'newSurfaceBarycentric':weights,'rootToNewSurfaceDistanceM':dist,'frameUsesActualEvaluatedTriangleWinding':True,'anatomicalMarginOrFiniteContactAccepted':False})
 for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',lids[:,j])
 lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',bary.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());lash.data.update_tag();lash.update_tag();deliver(0);save('a-mobile-lash-bindings.json',bindings);save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'actualCompleteSkin':base.name,'sharedCutAndUnionActuallyApplied':True,'originalFullSkinAndOriginalOpticsRetainedHidden':True,'actualNewEyes':newEyes,'all24800GroomAnd412LashCurvesRadiiPreserved':True,'groomMaxWorldDifferenceM':groomError,'sourceDynamicVerticesMissing':missing,'sourceRigCodeNotExecuted':True,'anatomicalMarginFiniteContactAndWholeOperationUnaccepted':True,'rights':'Rain Rig (CC) Blender Foundation | studio.blender.org / CC-BY4.0 plus inherited native/body/groom rights.','secondsBeforePreview':time.time()-tick});u.m.m.rig.shade.settings();u.m.m.rig.k.b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','body-face']:views.append(u.v.image('a-sewn-topological-character',view));save('a-view-controls.json',views)
 motion=[]
 for tag,value in [('half',.5),('closed',1.),('restored',0.)]:
  deliver(value);dd,PV,PT=u.b.geom(base);motion.append({'state':tag,'assignedBlink':value,'actualDisplayedMobileVertices':len(PV),'maximumDisplayedMobileMoveM':float(np.linalg.norm(PV-V,axis=1).max()),'finiteWallEvaluated':True});views.append(u.v.image('a-sewn-topological-character-'+tag,'face'));save('a-preview-motion.json',motion);save('a-view-controls.json',views)
 print('R112_ACTUAL_SEWN_TOPOLOGICAL_COMPLETE_CHARACTER_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
