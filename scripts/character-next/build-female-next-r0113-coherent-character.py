"""Whole coherent adult CC0 head, own closure topology and sewn neck on one woman."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0113-coherent-head-foundation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0107-b-native-pinned-lids.blend';OUT=S/'aevrynd-female-next-r0113-a-coherent-native-head.blend'
def mod(n,p):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
u=mod('r113union','build-female-next-r0104-native-head-union.py');q=u.q;u.v.E=E;oldbuild=mod('r113helpers','build-female-next-r0112-topological-character.py');author=mod('r113author','author-female-next-r0113-coherent-head.py')
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def deliver(value):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];face['blink_left']=face['blink_right']=value;face.update_tag()
 for ob in bpy.data.objects:
  if ob.name.startswith('AFN113_') and ob.type=='MESH' and ob.data.shape_keys:ob.data.shape_keys.update_tag();ob.update_tag()
 bpy.context.view_layer.update()
def sphere(P):
 a=np.c_[2*P,np.ones(len(P))];f=np.linalg.lstsq(a,np.sum(P*P,axis=1),rcond=None)[0];return f[:3],np.sqrt(f[3]+f[:3]@f[:3])
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 face['blink_left']=face['blink_right']=0.;oral['jaw_open']=0.;face.update_tag();oral.update_tag();bpy.context.view_layer.update();old=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];d,OW,OT=u.b.geom(old);OW=OW.copy();OT=OT.copy();ol=q.arr(d.loop_triangles,'loops',len(OT),3,dtype='i4');op=q.arr(d.loop_triangles,'polygon_index',len(OT),dtype='i4');ouv={x.name:q.arr(x.data,'uv',len(d.loops),2)[ol].copy() for x in d.uv_layers};hf=q.arr(d.attributes['AFN104_SourceHeadFace'].data,'value',len(d.polygons),dtype='i4');on=np.cross(OW[OT[:,1]]-OW[OT[:,0]],OW[OT[:,2]]-OW[OT[:,0]]);on/=np.maximum(np.linalg.norm(on,axis=1),1e-30)[:,None];sel=np.flatnonzero((hf[op]>=0)&(on[:,1]<-.05));uvtree=BVHTree.FromPolygons(OW.tolist(),OT[sel].tolist(),all_triangles=True)
 with bpy.data.libraries.load(str(E/'coherent-native-head-authoring.blend'),link=False) as (aa,bb):bb.objects=['AFN113_NATIVE_ADULT_FULL_HEAD_SOURCE']
 head=bb.objects[0];bpy.context.scene.collection.objects.link(head);head.hide_render=False;head.hide_set(False)
 # Read actual own evaluated head states, including its original UV seam data.
 hk=head.data.shape_keys.key_blocks
 for k in hk:k.value=0.
 head.data.shape_keys.update_tag();head.update_tag();bpy.context.view_layer.update();dd,H,HT=u.b.geom(head);H=H.copy();HT=HT.copy();hl=q.arr(dd.loop_triangles,'loops',len(HT),3,dtype='i4');nativeUV=q.arr(dd.uv_layers['MakeHumanOriginalUV'].data,'uv',len(dd.loops),2)[hl].copy();poses={}
 for side in ['L','R']:
  hk['AFN113_NATIVE_CLOSED_'+side].value=1.;head.data.shape_keys.update_tag();head.update_tag();bpy.context.view_layer.update();pd,P,PT=u.b.geom(head);poses[side]=P.copy();hk['AFN113_NATIVE_CLOSED_'+side].value=0.;head.data.shape_keys.update_tag();head.update_tag();bpy.context.view_layer.update()
 info=json.loads((E/'coherent-native-head.json').read_text('utf8'));VV,VU,FF,FUV,GG=author.load_mesh();VV+=author.target('macrodetails/caucasian-female-young.target.gz',len(VV));C=np.array(info['nativeEyeCentresWorld']);VV=VV[:,[0,2,1]]*np.array([1,-1,1])*info['uniformScale']+np.array(info['translation']);eyes=[];optical=[]
 for side,low in [('L','l'),('R','r')]:
  helper=np.unique(np.concatenate([f for f,g in zip(FF,GG) if g=='helper-'+low+'-eye']));_,targetR=sphere(VV[helper]);original=bpy.data.objects['AFN104_NATIVE_'+side+'_SCLERA'];gd,GP,GT=u.b.geom(original);oldC,oldR=sphere(GP.copy());factor=targetR/oldR
  for part in ['SCLERA','IRIS']:
   src=bpy.data.objects['AFN104_NATIVE_'+side+'_'+part];gd,GP,GT=u.b.geom(src);GP=GP.copy();GT=GT.copy();gl=q.arr(gd.loop_triangles,'loops',len(GT),3,dtype='i4');guv={x.name:q.arr(x.data,'uv',len(gd.loops),2)[gl].copy() for x in gd.uv_layers};gmi=q.arr(gd.polygons,'material_index',len(gd.polygons),dtype='i4')[q.arr(gd.loop_triangles,'polygon_index',len(GT),dtype='i4')];newP=(GP-oldC)*factor+C[0 if side=='L' else 1];me=bpy.data.meshes.new('AFN113_'+side+'_'+part);me.from_pydata(newP.tolist(),[],GT.tolist());me.update();ob=bpy.data.objects.new(me.name,me);bpy.context.scene.collection.objects.link(ob)
   for mat in src.data.materials:me.materials.append(mat)
   me.polygons.foreach_set('material_index',gmi);me.polygons.foreach_set('use_smooth',np.ones(len(GT),bool))
   for name,values in guv.items():me.uv_layers.new(name=name).data.foreach_set('uv',values.astype('f4').ravel())
   src.hide_render=True;src.hide_set(True);eyes.append(ob.name)
  optical.append({'side':side,'helperDerivedStagingRadiusM':targetR,'oldSphereFitCentre':oldC,'oldFitRadiusM':oldR,'uniformComponentScale':factor,'helperNotRenderedOrContactProof':True})
 # Inspect actual complete source head neutral/closed before using it as a base.
 savedVisibility={o.name:o.hide_render for o in bpy.context.scene.objects if o.type in ['MESH','CURVES','CURVE']}
 for name in savedVisibility:bpy.data.objects[name].hide_render=name not in [head.name]+eyes
 u.m.m.rig.shade.settings();u.m.m.rig.k.b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.scene.render.hair_subdiv=3;refs=[u.v.image('reference-coherent-native-head-neutral','face')]
 for side in ['L','R']:hk['AFN113_NATIVE_CLOSED_'+side].value=1.
 head.data.shape_keys.update_tag();head.update_tag();bpy.context.view_layer.update();refs.append(u.v.image('reference-coherent-native-head-closed','face'));save('source-reference-view-controls.json',refs)
 for side in ['L','R']:hk['AFN113_NATIVE_CLOSED_'+side].value=0.
 head.data.shape_keys.update_tag();head.update_tag()
 for name,value in savedVisibility.items():bpy.data.objects[name].hide_render=value
 head.hide_render=True;head.hide_set(True);bpy.context.view_layer.update()
 # Only the old head is replaced; body skin/UV/material data is retained below neck.
 body=old.copy();body.data=old.data.copy();bpy.context.scene.collection.objects.link(body);body.name='AFN113_COMPLETE_WOMAN_COHERENT_HEAD';body.shape_key_clear();A=np.array(body.matrix_world);AI=np.linalg.inv(A);local=lambda p:(p-A[:3,3])@AI[:3,:3].T
 bm=bmesh.new();bm.from_mesh(body.data);normal=A[:3,:3].T@np.array([0.,0.,1.]);normal/=np.linalg.norm(normal);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector(local(np.array([0.,0.,1.31]))),plane_no=Vector(normal),clear_inner=False,clear_outer=True,dist=1e-7);bm.to_mesh(body.data);bm.free();body.data.update();BL=q.arr(body.data.vertices,'co',len(body.data.vertices),3);BW=BL@A[:3,:3].T+A[:3,3]
 bloops=oldbuild.loops_from_faces([list(p.vertices) for p in body.data.polygons]);brow=min(bloops,key=lambda row:abs(np.mean(BW[row,2])-1.31));hloops=oldbuild.loops_from_faces(HT);hrow=min(hloops,key=lambda row:abs(np.mean(H[row,2])-1.31));assert max(abs(BW[brow,2]-1.31))<5e-6 and max(abs(H[hrow,2]-1.31))<5e-6
 # Continuous rest material mapping only, no pose transfer onto the old head.
 headUV={name:np.empty((len(H),2),'f4') for name in ouv};uvdist=[]
 for i,p in enumerate(H):
  hit,no,fi,dist=uvtree.find_nearest(Vector(p));ti=sel[fi];w=u.a.bary(np.array(hit),OW[OT[ti]]);uvdist.append(dist)
  for name in ouv:headUV[name][i]=w@ouv[name][ti]
 bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();nb=len(bm.verts);newV=[bm.verts.new(Vector(p)) for p in local(H)];bm.verts.index_update();bm.verts.ensure_lookup_table();uvlayers={name:bm.loops.layers.uv.get(name) or bm.loops.layers.uv.new(name) for name in ouv};nuv=bm.loops.layers.uv.new('MakeHumanOriginalUV')
 for ti,tri in enumerate(HT):
  f=bm.faces.new([newV[int(i)] for i in tri]);f.material_index=4;f.smooth=True
  for j,(loop,vi) in enumerate(zip(f.loops,tri)):
   for name,layer in uvlayers.items():loop[layer].uv=headUV[name][int(vi)]
   loop[nuv].uv=nativeUV[ti,j]
 area=lambda p:np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1])
 if area(BW[brow])*area(H[hrow])<0:hrow=list(reversed(hrow))
 phase=int(np.argmin(np.linalg.norm(BW[brow]-H[hrow[0]],axis=1)));brow=brow[phase:]+brow[:phase]
 def param(p):d=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);return np.r_[0,np.cumsum(d)/d.sum()]
 bt=param(BW[brow]);ht=param(H[hrow]);i=j=0;seam=0
 while i<len(brow) or j<len(hrow):
  bi=brow[i%len(brow)];hj=int(hrow[j%len(hrow)])
  if j==len(hrow) or (i<len(brow) and bt[i+1]<=ht[j+1]):tri=[bm.verts[bi],newV[hj],bm.verts[brow[(i+1)%len(brow)]]];i+=1
  else:tri=[bm.verts[bi],newV[hj],newV[int(hrow[(j+1)%len(hrow)])]];j+=1
  f=bm.faces.new(tri);f.material_index=4;f.smooth=True
  for loop in f.loops:
   p=np.array(body.matrix_world@loop.vert.co);hit,no,fi,dist=uvtree.find_nearest(Vector(p));w=u.a.bary(np.array(hit),OW[OT[sel[fi]]])
   for name,layer in uvlayers.items():loop[layer].uv=w@ouv[name][sel[fi]]
  seam+=1
 bm.to_mesh(body.data);bm.free();body.data.update();BL=q.arr(body.data.vertices,'co',len(body.data.vertices),3);sourceIDs=np.arange(nb,nb+len(H),dtype='i4');basis=body.shape_key_add(name='Basis',from_mix=False)
 for side,prop in [('L','blink_left'),('R','blink_right')]:
  key=body.shape_key_add(name='AFN113_CLOSED_'+side,from_mix=False);key.relative_key=basis;key.value=0.;P=BL.copy();P[sourceIDs]+=(poses[side]-H)@AI[:3,:3].T;key.data.foreach_set('co',P.astype('f4').ravel());oldbuild.drive(key,face,prop,'v')
 old.name='AFN113_PREVIOUS_COMPLETE_SKIN_REFERENCE';old.hide_render=True;old.hide_set(True);deliver(0);dd,W,T=u.b.geom(body);W=W.copy();T=T.copy();triHead=np.all(np.isin(T,sourceIDs),axis=1);centre=W[T].mean(1);normal=np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]]);normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-30)[:,None]
 # Rebind every existing fibre to this actual head; no missing fibres are removed.
 hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];H0=q.hair(hair).reshape(24800,17,3).copy();HA=np.array(hair.matrix_world);HI=np.linalg.inv(HA[:3,:3]);HL=(H0-HA[:3,3])@HI.T;cap=np.flatnonzero(triHead&((centre[:,2]>1.50)|((centre[:,2]>1.43)&(centre[:,1]>-.065))));scalpTree=BVHTree.FromPolygons(W.tolist(),T[cap].tolist(),all_triangles=True);VL=(W-HA[:3,3])@HI.T;ids=np.empty((24800,3),'i4');weights=np.empty((24800,3),'f4');rt=np.empty_like(weights);rb=np.empty_like(weights);rn=np.empty_like(weights);rr=np.empty_like(weights);radius=q.arr(hair.data.attributes['AFN97_RootRadiusNative'].data,'value',24800);gaps=[]
 for i,root in enumerate(H0[:,0]):
  hit,no,fi,dist=scalpTree.find_nearest(Vector(root));tri=T[cap[fi]];w=u.a.bary(np.array(hit),W[tri]);p=VL[tri];t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);ids[i]=tri;weights[i]=w;rt[i]=t;rb[i]=np.cross(n,t);rn[i]=n;rr[i]=w@p+n*radius[i];gaps.append(dist)
 copy=hair.copy();copy.data=hair.data.copy();bpy.context.scene.collection.objects.link(copy);copy.name='AFN113_PREVIOUS_COMPLETE_GROOM_REFERENCE';copy.hide_render=True;copy.hide_set(True);newHL=HL+(rr-HL[:,0])[:,None,:];hair.data.attributes['position'].data.foreach_set('vector',newHL.astype('f4').reshape(-1,3).ravel())
 for j in range(3):hair.data.attributes['AFN97_ScalpVertex'+str(j)].data.foreach_set('value',ids[:,j])
 for name,value in [('RootBarycentric',weights),('RestRoot',rr),('RestT',rt),('RestB',rb),('RestN',rn)]:hair.data.attributes['AFN97_'+name].data.foreach_set('vector',value.astype('f4').ravel())
 for md in list(hair.modifiers):hair.modifiers.remove(md)
 u.root_modifier(hair,body);hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();groom=q.hair(hair).reshape(H0.shape);groomError=float(np.linalg.norm(groom-(newHL@HA[:3,:3].T+HA[:3,3]),axis=2).max());assert groomError<6e-6
 lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];LH=q.geom(lash)[1].copy();LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);LV=(W-LA[:3,3])@LI.T;LL=(LH-LA[:3,3])@LI.T;choices=np.flatnonzero(triHead&(abs(centre[:,2]-C.mean(0)[2])<.020)&(centre[:,1]<C.mean(0)[1])&(normal[:,1]<-.1));lashTree=BVHTree.FromPolygons(W.tolist(),T[choices].tolist(),all_triangles=True);bindings=json.loads((E.parent/'r0107-native-coarse-lid-cage/b-native-seam-lash-bindings.json').read_text('utf8'));lids=np.empty((len(LH),3),'i4');bary=np.empty_like(LH);offset=np.empty_like(LH)
 for row in bindings:
  start=row['pointStart'];end=start+row['points'];hit,no,fi,dist=lashTree.find_nearest(Vector(LH[start]));tri=T[choices[fi]];p=LV[tri];w=u.a.bary((np.array(hit)-LA[:3,3])@LI.T,p);t=p[1]-p[0];t/=np.linalg.norm(t);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n);frame=np.column_stack((t,np.cross(n,t),n));lids[start:end]=tri;bary[start:end]=w;offset[start:end]=(LL[start:end]-LL[start])@frame;row.update(actualNewUnifiedSkinTriangle=tri,newSurfaceBarycentric=w,rootToNewSurfaceDistanceM=dist,frameUsesActualEvaluatedTriangleWinding=True,anatomicalMarginOrFiniteContactAccepted=False)
 for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',lids[:,j])
 lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',bary.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());oldbuild.node_retarget(lash,old,body);lash.data.update_tag();lash.update_tag();deliver(0);save('a-mobile-lash-bindings.json',bindings)
 np.savez_compressed(E/'whole-head-source-correspondence.npz',sourceHeadToBody=sourceIDs,sourceNeutralWorld=H,sourceClosedL=poses['L'],sourceClosedR=poses['R'],originalGroomWorld=H0,newGroomWorld=groom,scalpTriangleIDs=cap)
 save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'actualWholeHeadSource':'MakeHuman/MPFB core adult female CC0, native closure targets, no old-head pose transfer or local donor graft','newHeadVertices':len(H),'actualCompleteSkinVertices':len(W),'actualCompleteTriangles':len(T),'neckBodyRimVertices':len(brow),'neckHeadRimVertices':len(hrow),'explicitNeckBridgeTriangles':seam,'originalSkinMaterialSlotsRetained':True,'all24800GroomAnd412LashCurvesRadiiRetained':True,'groomActualMaxAgainstAuthoredTranslatedFibresM':groomError,'groomRootTranslationQuantilesM':np.quantile(np.linalg.norm(groom[:,0]-H0[:,0],axis=1),[0,.5,.95,1]),'scalpDomain':'Geometric authoring cap on actual new whole head, anatomical follicle/contact proof unaccepted.','sourceMaterialMappingDistanceQuantilesM':np.quantile(uvdist,[0,.5,.95,1]),'eyes':optical,'sourceReferences':'source-reference-view-controls.json','oldWholeSkinAndGroomRetainedHidden':True,'bodyRigGuideBrowsOralControlsAndCompleteFiniteContactRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick})
 u.m.m.rig.shade.settings();u.m.m.rig.k.b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','body-face']:views.append(u.v.image('a-coherent-native-character',view));save('a-view-controls.json',views)
 motion=[]
 for label,value in [('half',.5),('closed',1.),('restored',0.)]:
  deliver(value);dd,P,PT=u.b.geom(body);motion.append({'state':label,'assignedBlink':value,'actualSkinMaximumMoveM':float(np.linalg.norm(P-W,axis=1).max())});views.append(u.v.image('a-coherent-native-character-'+label,'face'));save('a-preview-motion.json',motion);save('a-view-controls.json',views)
 print('R113_COHERENT_WHOLE_HEAD_COMPLETE_CHARACTER_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
