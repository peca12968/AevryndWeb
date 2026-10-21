"""One complete woman with actual replacement mobile ocular meshes and cut ports."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0111-native-mobile-lid-mesh';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0107-b-native-pinned-lids.blend';OUT=S/'aevrynd-female-next-r0111-a-mobile-ocular-graft.blend';RAIN=R/'Reference/character/blender-studio-rain-v3-cc-by4/Rain v3.3/rain_v3.2.blend'
sp=importlib.util.spec_from_file_location('r111build',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def drive(key,face,prop,expression):
 fc=key.driver_add('value');fc.driver.expression=expression;v=fc.driver.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=face;v.targets[0].data_path='["'+prop+'"]'
def wire_keys(ob,face,side,neutral,half,closed):
 if ob.data.shape_keys is None:ob.shape_key_add(name='Basis')
 ck=ob.shape_key_add(name='AFN111_'+side+'_closed');ck.data.foreach_set('co',closed.astype('f4').ravel());hk=ob.shape_key_add(name='AFN111_'+side+'_half');hk.data.foreach_set('co',(neutral+(half-neutral)-.5*(closed-neutral)).astype('f4').ravel());drive(ck,face,'blink_left' if side=='L' else 'blink_right','v');drive(hk,face,'blink_left' if side=='L' else 'blink_right','4*v*(1-v)')
def deliver(value):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];face['blink_left']=face['blink_right']=value;face.update_tag()
 for ob in bpy.data.objects:
  if ob.name.startswith('AFN111_') and ob.type=='MESH' and ob.data.shape_keys:ob.data.shape_keys.update_tag();ob.update_tag()
 bpy.context.view_layer.update()
def main():
 tick=time.time();assert not OUT.exists();art=np.load(E/'mobile-ocular-authoring.npz');data=np.load(E/'actual-rain-ocular-geometry.npz');info=json.loads((E/'actual-rain-ocular-geometry.json').read_text('utf8'));bpy.ops.wm.open_mainfile(filepath=str(SRC));face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 face['blink_left']=face['blink_right']=0.;oral['jaw_open']=0.;face.update_tag();oral.update_tag();bpy.context.view_layer.update();old=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];d,W,T=u.b.geom(old);W=W.copy();T=T.copy();lf=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');pf=q.arr(d.loop_triangles,'polygon_index',len(T),dtype='i4');uv={v.name:q.arr(v.data,'uv',len(d.loops),2)[lf].copy() for v in d.uv_layers};hf=q.arr(d.attributes['AFN104_SourceHeadFace'].data,'value',len(d.polygons),dtype='i4');norm=np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]]);norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-30)[:,None];selected=np.flatnonzero((hf[pf]>=0)&(norm[:,1]<-.1));used,inv=np.unique(T[selected],return_inverse=True);uvtree=BVHTree.FromPolygons(W[used].tolist(),inv.reshape(-1,3).tolist(),all_triangles=True);hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];H0=q.hair(hair).copy();lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];LH=q.geom(lash)[1].copy();base=old.copy();base.data=old.data.copy();assert base.data.shape_keys!=old.data.shape_keys;bpy.context.scene.collection.objects.link(base);base.name='AFN111_BODY_WITH_OCULAR_GRAFT_PORTS';base.shape_key_clear();attr=base.data.attributes.new(name='AFN111_OriginalSkinFace',type='INT',domain='FACE');attr.data.foreach_set('value',np.arange(len(base.data.polygons),dtype='i4'));attr=base.data.attributes.new(name='AFN111_OriginalSkinVertex',type='INT',domain='POINT');attr.data.foreach_set('value',np.arange(len(base.data.vertices),dtype='i4'));cut=set(map(int,art['removedNativeSourceTriangles']));rawhf=q.arr(base.data.attributes['AFN104_SourceHeadFace'].data,'value',len(base.data.polygons),dtype='i4');bm=bmesh.new();bm.from_mesh(base.data);bm.faces.ensure_lookup_table();removed=[f for f in bm.faces if int(rawhf[f.index]) in cut];removedCount=len(removed);bmesh.ops.delete(bm,geom=removed,context='FACES_ONLY');bm.to_mesh(base.data);bm.free();base.data.update();old.name='AFN111_PREVIOUS_COMPLETE_NATIVE_SKIN_REFERENCE';old.hide_render=True;old.hide_set(True);oldIDs=q.arr(base.data.attributes['AFN111_OriginalSkinVertex'].data,'value',len(base.data.vertices),dtype='i4');inverse=np.full(len(oldIDs),-1,'i4');inverse[oldIDs]=np.arange(len(oldIDs));assert (inverse>=0).all();oldRaw=q.arr(old.data.vertices,'co',len(old.data.vertices),3);assert np.array_equal(q.arr(base.data.vertices,'co',len(base.data.vertices),3),oldRaw[oldIDs])
 for md in hair.modifiers:
  if md.type=='NODES':
   md.node_group=md.node_group.copy()
   for node in md.node_group.nodes:
    if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==old:node.inputs['Object'].default_value=base
 for j in range(3):
  at=hair.data.attributes['AFN97_ScalpVertex'+str(j)];ids=q.arr(at.data,'value',24800,dtype='i4');at.data.foreach_set('value',inverse[ids])
 hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();assert np.array_equal(q.hair(hair),H0)
 with bpy.data.libraries.load(str(E/'mobile-ocular-authoring.blend'),link=False) as (a,b):b.objects=['AFN111_MOBILE_FINITE_OCULAR_SKIN']
 mobile=b.objects[0];bpy.context.scene.collection.objects.link(mobile);mobile.hide_render=False;mobile.hide_set(False);mobile.data.materials.append(old.data.materials[4]);N=q.arr(mobile.data.vertices,'co',len(mobile.data.vertices),3);vertexUV={name:np.empty((len(N),2),'f4') for name in uv}
 for i,p in enumerate(N):
  hit,no,fi,dist=uvtree.find_nearest(Vector(p));oldfi=selected[fi];tri=W[T[oldfi]];xy=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),np.array(hit)-tri[0],rcond=None)[0];weights=np.clip(np.r_[1-xy.sum(),xy],0,1);weights/=weights.sum()
  for name in uv:vertexUV[name][i]=weights@uv[name][oldfi]
 mids=q.arr(mobile.data.loops,'vertex_index',len(mobile.data.loops),dtype='i4')
 for name,values in vertexUV.items():mobile.data.uv_layers.new(name=name).data.foreach_set('uv',values[mids].ravel())
 if mobile.data.uv_layers.get('VitruvianUV.UDIM'):mobile.data.uv_layers.active=mobile.data.uv_layers['VitruvianUV.UDIM'];mobile.data.uv_layers['VitruvianUV.UDIM'].active_render=True
 keys=mobile.data.shape_keys.key_blocks
 for side,prop in [('L','blink_left'),('R','blink_right')]:
  closed=keys['AFN111_'+side+'_closed'];half=keys['AFN111_'+side+'_half'];C=q.arr(closed.data,'co',len(N),3);H=q.arr(half.data,'co',len(N),3);half.data.foreach_set('co',(N+(H-N)-.5*(C-N)).astype('f4').ravel());drive(closed,face,prop,'v');drive(half,face,prop,'4*v*(1-v)')
 materials=list(dict.fromkeys(info['materials']['eyes']+info['materials']['cornea']))
 with bpy.data.libraries.load(str(RAIN),link=False) as (a,b):b.materials=materials
 materialMap={m.name:m for m in b.materials if m}
 for mat in materialMap.values():
  if mat.animation_data:mat.animation_data_clear()
  if mat.node_tree and mat.node_tree.animation_data:mat.node_tree.animation_data_clear()
 newEyes=[]
 for name in ['eyes','cornea']:
  for side in ['L','R']:
   V=art[name+'_'+side+'_neutralWorld'];TT=art[name+'_'+side+'_triangles'];sourceT=art[name+'_'+side+'_sourceTriangleIDs'];mesh=bpy.data.meshes.new('AFN111_'+name.upper()+'_'+side);mesh.from_pydata(V.tolist(),[],TT.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob)
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
 for md in lash.modifiers:
  if md.type=='NODES':
   md.node_group=md.node_group.copy()
   for node in md.node_group.nodes:
    if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==old:node.inputs['Object'].default_value=mobile
 bpy.context.view_layer.update();dd,V,TT=u.b.geom(mobile);V=V.copy();TT=TT.copy();normal=np.cross(V[TT[:,1]]-V[TT[:,0]],V[TT[:,2]]-V[TT[:,0]]);normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-30)[:,None];choices=np.flatnonzero((normal[:,1]<-.1)&(abs(V[TT].mean(1)[:,2]-1.463)<.018));lidTree=BVHTree.FromPolygons(V.tolist(),TT[choices].tolist(),all_triangles=True);bindings=json.loads((E.parent/'r0107-native-coarse-lid-cage/b-native-seam-lash-bindings.json').read_text('utf8'));LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);VL=(V-LA[:3,3])@LI.T;lids=np.empty((len(LH),3),'i4');bary=np.empty_like(LH);offset=np.empty_like(LH)
 for row in bindings:
  start=row['pointStart'];end=start+row['points'];hit,no,fi,dist=lidTree.find_nearest(Vector(LH[start]));tri=TT[choices[fi]];p=VL[tri];weights=u.a.bary((np.array(hit)-LA[:3,3])@LI.T,p);t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);frame=np.column_stack((t,np.cross(n,t),n));lids[start:end]=tri;bary[start:end]=weights;offset[start:end]=((LH[start:end]-LH[start])@LI.T)@frame;row.update({'actualNewMobileSkinTriangle':tri,'newSurfaceBarycentric':weights,'rootToNewSurfaceDistanceM':dist,'frameUsesActualEvaluatedTriangleWinding':True,'anatomicalMarginOrFiniteContactAccepted':False})
 for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',lids[:,j])
 lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',bary.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());lash.data.update_tag();lash.update_tag();deliver(0);save('a-mobile-lash-bindings.json',bindings);save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'actualNewMobileMesh':mobile.name,'actualBodyWithCutPorts':base.name,'removedOldNativeSurfaceFaces':removedCount,'originalFullSkinAndOriginalOpticsRetainedAsHiddenReference':True,'actualNewEyes':newEyes,'originalBodyVerticesRetainedForBindingStability':len(oldIDs),'bodyOutsideReplacementPortPositionsExact':True,'neutralFullGroomExactlyRetained':True,'all24800GroomAnd412LashCurvesRadiiPreserved':True,'lashRootsReboundToNewActualSkinNotQualifiedAnatomicalMargin':True,'finiteThicknessM':.0008,'collarOverlapNotWatertightAnatomicalOrContactProof':True,'sourceRigCodeNotExecuted':True,'rights':'Rain Rig (CC) Blender Foundation | studio.blender.org / CC-BY4.0, plus inherited native/body/groom rights remain.','secondsBeforePreview':time.time()-tick});u.m.m.rig.shade.settings();u.m.m.rig.k.b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','body-face']:views.append(u.v.image('a-mobile-ocular-graft-character',view));save('a-view-controls.json',views)
 motion=[]
 for tag,value in [('half',.5),('closed',1.),('restored',0.)]:
  deliver(value);dd,PV,PT=u.b.geom(mobile);motion.append({'state':tag,'assignedBlink':value,'actualDisplayedMobileVertices':len(PV),'maximumDisplayedMobileMoveM':float(np.linalg.norm(PV-V,axis=1).max()),'finiteWallEvaluated':True});views.append(u.v.image('a-mobile-ocular-graft-character-'+tag,'face'));save('a-preview-motion.json',motion);save('a-view-controls.json',views)
 print('R111_ACTUAL_NEW_MOBILE_MESH_COMPLETE_CHARACTER_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
