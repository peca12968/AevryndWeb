"""Actual native artist head joined by closed-volume intersection, not a collar.
Complete static art candidate first; original control sources/rollback remain.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0104-native-artist-ocular-foundation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0104-a-native-artist-ocular.blend';OUT=S/'aevrynd-female-next-r0104-b-native-head-volume-union.blend'
sp=importlib.util.spec_from_file_location('r104union',Path(__file__).with_name('build-female-next-r0104-native-ocular.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;v=a.v;v.E=E;m=b.m
def save(n,x):a.save(n,x)
def cut(mesh,z,above):
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=above,clear_outer=not above,dist=1e-7);boundary=[edge for edge in bm.edges if edge.is_boundary]
 if boundary:
  result=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
  for face in result['faces']:face.material_index=4
 bm.to_mesh(mesh);bm.free();mesh.update();return len(boundary)
def root_modifier(hair,body):
 ng,n,L=m.interface('AFN104_NATIVE_REST_CURVES_ON_ACTUAL_UNION_SKIN');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=body;pos=n.new('GeometryNodeInputPosition')
 def attr(name,kind='FLOAT_VECTOR'):
  at=n.new('GeometryNodeInputNamedAttribute');at.data_type=kind;at.inputs['Name'].default_value='AFN97_'+name;return at.outputs['Attribute']
 def vec(op,x,y=None,s=None):
  nd=n.new('ShaderNodeVectorMath');nd.operation=op;L.new(x,nd.inputs[0])
  if y is not None:L.new(y,nd.inputs[1])
  if s is not None:L.new(s,nd.inputs['Scale'])
  return nd.outputs['Vector']
 pp=[]
 for j in range(3):
  nd=n.new('GeometryNodeSampleIndex');nd.data_type='FLOAT_VECTOR';nd.domain='POINT';L.new(info.outputs['Geometry'],nd.inputs['Geometry']);L.new(pos.outputs['Position'],nd.inputs['Value']);L.new(attr('ScalpVertex'+str(j),'INT'),nd.inputs['Index']);pp.append(nd.outputs['Value'])
 t=vec('NORMALIZE',vec('SUBTRACT',pp[1],pp[0]));normal=vec('NORMALIZE',vec('CROSS_PRODUCT',vec('SUBTRACT',pp[1],pp[0]),vec('SUBTRACT',pp[2],pp[0])));bit=vec('CROSS_PRODUCT',normal,t);sep=n.new('ShaderNodeSeparateXYZ');L.new(attr('RootBarycentric'),sep.inputs[0]);terms=[vec('SCALE',pp[j],s=sep.outputs[j]) for j in range(3)];root=vec('ADD',vec('ADD',terms[0],terms[1]),vec('ADD',terms[2],vec('SCALE',normal,s=attr('RootRadiusNative','FLOAT'))));offset=vec('SUBTRACT',pos.outputs['Position'],attr('RestRoot'));terms=[]
 for direction,name in [(t,'RestT'),(bit,'RestB'),(normal,'RestN')]:
  dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';L.new(offset,dot.inputs[0]);L.new(attr(name),dot.inputs[1]);terms.append(vec('SCALE',direction,s=dot.outputs['Value']))
 setpos=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(vec('ADD',root,vec('ADD',terms[0],vec('ADD',terms[1],terms[2]))),setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=hair.modifiers.new('AFN104_ACTUAL_UNION_SKIN_ROOT_FRAMES','NODES');md.node_group=ng
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();native=bpy.data.objects['AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN'];hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];d,C,CT=b.geom(native);C=C.copy();CT=CT.copy();d.calc_loop_triangles();cl=q.arr(d.loop_triangles,'loops',len(CT),3,dtype='i4');uvs={u.name:q.arr(u.data,'uv',len(u.data),2)[cl].copy() for u in d.uv_layers};sourceMat=q.arr(d.polygons,'material_index',len(d.polygons),dtype='i4')[q.arr(d.loop_triangles,'polygon_index',len(CT),dtype='i4')];canonical=list(native.data.materials);A=np.array(native.matrix_world);AI=np.linalg.inv(A[:3,:3]);local=lambda P:(P-A[:3,3])@AI.T;tree=BVHTree.FromPolygons(C.tolist(),CT.tolist(),all_triangles=True);ref=np.load(E/'animation-actual-source-geometry.npz');target=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];centres=np.array([target[s]['posteriorSphereFitCentreWorld'] for s in ['L','R']]);centre=centres.mean(0);scale=np.linalg.norm(centres[0]-centres[1])/.060;P=(ref['world']-centre)*scale+centre;HT=ref['triangles'];headMesh=bpy.data.meshes.new('AFN104_ORIGINAL_ANIMATION_HEAD_SURFACE');headMesh.from_pydata(local(P).tolist(),[],HT.tolist());headMesh.update()
 for material in canonical:headMesh.materials.append(material)
 pointUV={name:np.empty((len(P),2),'f4') for name in uvs};distances=[]
 for i,p in enumerate(P):
  hit,no,fi,dist=tree.find_nearest(Vector(p));weights=a.bary(np.array(hit),C[CT[fi]]);distances.append(dist)
  for name,data in uvs.items():pointUV[name][i]=weights@data[fi]
 for name,data in pointUV.items():headMesh.uv_layers.new(name=name).data.foreach_set('uv',data[HT].ravel())
 headMats=[]
 for p in P[HT].mean(1):headMats.append(sourceMat[tree.find_nearest(Vector(p))[2]])
 headMesh.polygons.foreach_set('material_index',np.array(headMats,'i4'));headMesh.polygons.foreach_set('use_smooth',np.ones(len(HT),bool));headMesh.attributes.new('AFN104_OriginalCFace','INT','FACE').data.foreach_set('value',np.full(len(HT),-1,'i4'));headMesh.attributes.new('AFN104_SourceHeadFace','INT','FACE').data.foreach_set('value',np.arange(len(HT),dtype='i4'));head=bpy.data.objects.new('AFN104_NATIVE_HEAD_UNION_INPUT',headMesh);scene.collection.objects.link(head);head.matrix_world=native.matrix_world.copy();head.hide_render=True;cutHead=cut(headMesh,(1.30-A[2,3])/A[2,2],True)
 bodyMesh=bpy.data.meshes.new_from_object(native.evaluated_get(bpy.context.evaluated_depsgraph_get()),preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());bodyMesh.materials.clear()
 for material in canonical:bodyMesh.materials.append(material)
 bodyMesh.attributes.new('AFN104_OriginalCFace','INT','FACE').data.foreach_set('value',np.arange(len(bodyMesh.polygons),dtype='i4'));bodyMesh.attributes.new('AFN104_SourceHeadFace','INT','FACE').data.foreach_set('value',np.full(len(bodyMesh.polygons),-1,'i4'));cutBody=cut(bodyMesh,(1.345-A[2,3])/A[2,2],False);body=bpy.data.objects.new('AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD',bodyMesh);scene.collection.objects.link(body);body.matrix_world=native.matrix_world.copy();md=body.modifiers.new('AFN104_EXACT_CLOSED_VOLUME_HEAD_NECK_UNION','BOOLEAN');md.operation='UNION';md.solver='EXACT';md.object=head
 for ob in bpy.context.selected_objects:ob.select_set(False)
 body.select_set(True);bpy.context.view_layer.objects.active=body;bpy.context.view_layer.update();bpy.ops.object.modifier_apply(modifier=md.name);head.hide_set(True);native.hide_render=True;native.hide_set(True);bodyMesh=body.data
 # Local neck junction sculpt: true union has no separate zipper/collar.
 bm=bmesh.new();bm.from_mesh(bodyMesh);neck=[p for p in bm.verts if 1.305<float((body.matrix_world@p.co).z)<1.375]
 for _ in range(12):bmesh.ops.smooth_vert(bm,verts=neck,factor=.35,use_axis_x=True,use_axis_y=True,use_axis_z=True)
 bm.to_mesh(bodyMesh);bm.free();bodyMesh.update()
 for face in bodyMesh.polygons:face.use_smooth=True
 bodyMesh.uv_layers.active=bodyMesh.uv_layers['VitruvianUV.UDIM'];bodyMesh.uv_layers['VitruvianUV.UDIM'].active_render=True;bpy.context.view_layer.update();dd,W,T=b.geom(body);W=W.copy();T=T.copy();assert np.isfinite(W).all();headTags=q.arr(dd.attributes['AFN104_SourceHeadFace'].data,'value',len(dd.polygons),dtype='i4');triHead=headTags[q.arr(dd.loop_triangles,'polygon_index',len(T),dtype='i4')]>=0;triCentre=W[T].mean(1);scalp=np.flatnonzero(triHead&((triCentre[:,2]>centre[2]+.012)|((triCentre[:,2]>centre[2]-.012)&(triCentre[:,1]>centre[1]+.015))));assert len(scalp)>100;scalpTree=BVHTree.FromPolygons(W.tolist(),T[scalp].tolist(),all_triangles=True);H0=q.hair(hair).reshape(24800,17,3);HA=np.array(hair.matrix_world);HI=np.linalg.inv(HA[:3,:3]);HL=(H0-HA[:3,3])@HI.T;VL=(W-HA[:3,3])@HI.T;radius=q.arr(hair.data.attributes['AFN97_RootRadiusNative'].data,'value',24800);ids=np.empty((24800,3),'i4');weights=np.empty((24800,3),'f4');rt=np.empty((24800,3),'f4');rb=rt.copy();rn=rt.copy();rr=rt.copy();gaps=[]
 for i,root in enumerate(H0[:,0]):
  hit,no,fi,dist=scalpTree.find_nearest(Vector(root));tri=T[scalp[fi]];w=a.bary(np.array(hit),W[tri]);p=VL[tri];t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);ids[i]=tri;weights[i]=w;rt[i]=t;rb[i]=np.cross(n,t);rn[i]=n;rr[i]=w@p+n*radius[i];gaps.append(dist)
 reference=hair.copy();reference.data=hair.data.copy();scene.collection.objects.link(reference);reference.name='AFN104_REFERENCE_SOURCE_COMPLETE_GROOM';reference.hide_render=True;reference.hide_set(True);newHL=HL+(rr-HL[:,0])[:,None,:];hair.data.attributes['position'].data.foreach_set('vector',newHL.astype('f4').reshape(-1,3).ravel())
 for j in range(3):hair.data.attributes['AFN97_ScalpVertex'+str(j)].data.foreach_set('value',ids[:,j])
 for name,value in [('RootBarycentric',weights),('RestRoot',rr),('RestT',rt),('RestB',rb),('RestN',rn)]:hair.data.attributes['AFN97_'+name].data.foreach_set('vector',value.astype('f4').ravel())
 for md in list(hair.modifiers):hair.modifiers.remove(md)
 root_modifier(hair,body);hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();groom=q.hair(hair).reshape(H0.shape);groomError=float(np.linalg.norm(groom-(newHL@HA[:3,:3].T+HA[:3,3]),axis=2).max());assert groomError<6e-6,groomError
 # Original lashes follow newly selected anterior native-head triangles.
 H=q.geom(lash)[1];LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);LV=(W-LA[:3,3])@LI.T;LH=(H-LA[:3,3])@LI.T;normal=np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]]);normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-30)[:,None];selected=np.flatnonzero(triHead&(abs(triCentre[:,2]-centre[2])<.018)&(triCentre[:,1]<centre[1])&(normal[:,1]<-.1));lashTree=BVHTree.FromPolygons(W.tolist(),T[selected].tolist(),all_triangles=True);bindings=json.loads((E/'a-retained-lash-bindings.json').read_text('utf8'));lidIDs=np.empty((len(H),3),'i4');lb=np.empty_like(LH);offset=np.empty_like(LH)
 for row in bindings:
  start=row['pointStart'];end=start+row['points'];hit,no,fi,dist=lashTree.find_nearest(Vector(H[start]));tri=T[selected[fi]];w=a.bary(np.array(hit),W[tri]);p=LV[tri];t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);lidIDs[start:end]=tri;lb[start:end]=w;offset[start:end]=(LH[start:end]-LH[start])@np.column_stack((t,np.cross(n,t),n));row.update({'actualSkinTriangle':tri.tolist(),'barycentric':w.tolist(),'sourceRootToNewMarginDistanceWorldM':dist,'actualAnatomicalMarginAccepted':False})
 for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',lidIDs[:,j])
 lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',lb.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel())
 for md in lash.modifiers:
  if md.type=='NODES':
   md.node_group=md.node_group.copy()
   for node in md.node_group.nodes:
    if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==native:node.inputs['Object'].default_value=body
 lash.data.update_tag();lash.update_tag();bpy.context.view_layer.update();save('b-retained-lash-bindings.json',bindings);np.savez_compressed(E/'b-native-head-union-lineage.npz',actualWorld=W,triangles=T,nativeHeadTriangleMask=triHead,authoredScalpTriangleIDs=scalp,hairRootTriangleIDs=ids,hairRootBarycentric=weights,originalGroomWorld=H0,newGroomWorld=groom)
 save('b-build-summary.json',{'source':str(SRC),'output':str(OUT),'renderSkin':body.name,'sourceHead':'Head (Animation) - Realistic / Dan Ulrich / CC0','originalNativeHeadGeometryUsed':True,'nativeHeadDisplayStageIPDAdjustment':scale,'bodyCutWorldZ':1.345,'headCutWorldZ':1.30,'closedVolumeUnion':'Blender EXACT Boolean UNION after actual cut-loop capping, then12 local neck smoothing operations; no independently zipped boundary loops.','cutBoundaryEdges':{'body':cutBody,'head':cutHead},'nativeHeadUVTransferMaximumNearestOldSkinDistanceM':max(distances),'actualVertices':len(W),'actualTriangles':len(T),'groomAllOriginalCurvesAndWidthsRetained':True,'groomRootAuthoringRegion':'Actual source-head faces, upper/posterior geometric cap; authoring approximation, not proven anatomical follicles.','groomRootTransferWorldDistanceQuantilesM':np.quantile(gaps,[0,.5,.95,1]),'groomNativeRestReadbackMaximumWorldErrorM':groomError,'newActualSkinIsStaticArtCandidate':True,'originalBodyRigAndGuideSourcesRetainedButNewSkinDeformationAndGuideLinkUnaccepted':True,'completeAppearanceOperationContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 body['scope']='Complete same female body with actual native animation head, true closed-volume neck union and local neck sculpture. Static art candidate first; all original control/source objects and R102 rollbacks retained. New body skinning, native blink, guide editing, anatomical follicles, finite/self/continuous contacts and runtime unaccepted.';m.m.rig.shade.settings();m.m.rig.k.b.camera('face');scene.camera.data.lens=85;scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','profile','body-face']:views.append(v.image('b-native-head-union',view));save('b-view-controls.json',views)
 print('R104_B_NATIVE_HEAD_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
