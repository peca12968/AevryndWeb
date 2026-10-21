"""Put native coarse-sculpt poses onto the same complete r105 woman."""
from pathlib import Path
from collections import Counter
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0107-native-coarse-lid-cage';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0105-a-native-lip-chart.blend';OUT=S/'aevrynd-female-next-r0107-a-native-coarse-lids.blend'
sp=importlib.util.spec_from_file_location('r107assembly',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def deliver(value):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];face['blink_left']=face['blink_right']=value;face.update_tag();skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];skin.data.shape_keys.update_tag();skin.update_tag();bpy.context.view_layer.update()
def main():
 tick=time.time();assert not OUT.exists();data=np.load(E/'native-coarse-lid-poses.npz');P=data['neutralFineWorld'];T=data['fineTriangles'];poseArrays={key:data[key+'_fineDelta'].copy() for key in ['L_half','L_closed','R_half','R_closed']};ref=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');assert np.array_equal(T,ref['triangles']);bpy.ops.wm.open_mainfile(filepath=str(SRC));face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 face['blink_left']=face['blink_right']=0.;oral['jaw_open']=0.;face.update_tag();oral.update_tag();bpy.context.view_layer.update();skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];raw=skin.data;dd,W,TT=u.b.geom(skin);W=W.copy();TT=TT.copy();originalUV=q.arr(raw.uv_layers['VitruvianUV.UDIM'].data,'uv',len(raw.loops),2).copy();H0=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).copy();A=np.array(skin.matrix_world);AI=np.linalg.inv(A[:3,:3]);base=q.arr(raw.vertices,'co',len(raw.vertices),3);hf=q.arr(raw.attributes['AFN104_SourceHeadFace'].data,'value',len(raw.polygons),dtype='i4');starts=q.arr(raw.polygons,'loop_start',len(raw.polygons),dtype='i4');counts=q.arr(raw.polygons,'loop_total',len(raw.polygons),dtype='i4');ids=q.arr(raw.loops,'vertex_index',len(raw.loops),dtype='i4');headFaces=np.flatnonzero(hf>=0);deltas={key:np.zeros_like(W) for key in ['L_half','L_closed','R_half','R_closed']}
 for f in headFaces:
  fi=hf[f];vi=ids[starts[f]:starts[f]+counts[f]];tri=P[T[fi]];xy=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),(W[vi]-tri[0]).T,rcond=None)[0].T;weights=np.c_[1-xy.sum(1),xy]
  for key in deltas:deltas[key][vi]=weights@poseArrays[key][T[fi]]
 skin.shape_key_add(name='Basis')
 for side,prop in [('L','blink_left'),('R','blink_right')]:
  for label,delta,expression in [('Closed',deltas[side+'_closed'],'v'),('HalfCorrection',deltas[side+'_half']-.5*deltas[side+'_closed'],'4*v*(1-v)')]:
   key=skin.shape_key_add(name='AFN107_'+label+'_'+side);key.data.foreach_set('co',(base+delta@AI.T).astype('f4').ravel());fc=key.driver_add('value');fc.driver.expression=expression;var=fc.driver.variables.new();var.name='v';var.type='SINGLE_PROP';var.targets[0].id=face;var.targets[0].data_path='["'+prop+'"]'
 with bpy.data.libraries.load(str(E/'native-coarse-authoring.blend'),link=False) as (a,b):b.objects=['AFN107_ORIGINAL_COARSE_LID_AUTHORING_CAGE']
 cage=b.objects[0];bpy.context.scene.collection.objects.link(cage);cage.hide_render=True;cage.hide_set(True)
 # Preserve every original lash; use actual body triangle winding for its frame.
 nativeUV=np.load(E.parent/'r0105-native-head-skin-chart/actual-lip-and-native-chart.npz')['nativeUV-UVMap'];front=np.all((nativeUV[:,:,1]>.5)&(nativeUV[:,:,0]>.2)&(nativeUV[:,:,0]<.8),1);edgeRows=[]
 for fi in np.flatnonzero(front):
  for j,k in [(0,1),(1,2),(2,0)]:edgeRows.append((tuple(sorted((int(T[fi,j]),int(T[fi,k])))),int(fi)))
 edgeCounts=Counter(x[0] for x in edgeRows);seams={};bodyFace={int(hf[f]):int(f) for f in headFaces};headIDs=np.unique(np.concatenate([ids[starts[f]:starts[f]+counts[f]] for f in headFaces]));kd=KDTree(len(headIDs))
 for i in headIDs:kd.insert(Vector(W[i]),int(i))
 kd.balance();nativeBody={}
 for side,sign in [('L',1),('R',-1)]:
  seams[side]=[(edge,fi) for edge,fi in edgeRows if edgeCounts[edge]==1 and np.all((P[list(edge),2]>1.44)&(P[list(edge),2]<1.485)&(P[list(edge),0]*sign>.008)&(P[list(edge),0]*sign<.055)&(P[list(edge),1]<-.10))];assert len(seams[side])==40
  for edge,fi in seams[side]:
   for vertex in edge:
    _,bodyID,error=kd.find(Vector(P[vertex]));assert error<4e-6,error;nativeBody[vertex]=bodyID
 lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];LH=q.geom(lash)[1].copy();LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);VL=(W-LA[:3,3])@LI.T;bindings=json.loads((E.parent/'r0104-native-artist-ocular-foundation/b-retained-lash-bindings.json').read_text('utf8'));lids=np.empty((len(LH),3),'i4');bary=np.empty_like(LH);offset=np.empty_like(LH);errors=[]
 for row in bindings:
  start=row['pointStart'];end=start+row['points'];point=LH[start];side='L' if point[0]>0 else 'R';best=None
  for (a,b),fi in seams[side]:
   pa,pb=P[a],P[b];t=float(np.clip(np.dot(point-pa,pb-pa)/np.dot(pb-pa,pb-pa),0,1));error=float(np.linalg.norm(point-(pa+t*(pb-pa))))
   if best is None or error<best[0]:best=(error,a,b,fi,t)
  error,a,b,fi,t=best;f=bodyFace[fi];tri=list(map(int,ids[starts[f]:starts[f]+counts[f]]));assert len(tri)==3;aa,bb=nativeBody[a],nativeBody[b];weights=np.zeros(3);weights[tri.index(aa)]=1-t;weights[tri.index(bb)]=t;p=VL[tri];tangent=p[1]-p[0];tangent/=np.linalg.norm(tangent);normal=np.cross(p[1]-p[0],p[2]-p[0]);normal/=np.linalg.norm(normal);frame=np.column_stack((tangent,np.cross(normal,tangent),normal));lids[start:end]=tri;bary[start:end]=weights;offset[start:end]=((LH[start:end]-LH[start])@LI.T)@frame;errors.append(error);row.update({'nativeSourceUVSeamEdge':[int(a),int(b)],'actualSkinTriangle':tri,'barycentric':weights,'frameFollowsActualSkinTriangleWinding':True,'neutralRootPlacementChangeM':error,'anatomicalMarginAndFiniteContactAccepted':False})
 for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',lids[:,j])
 lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',bary.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());lash.data.update_tag();lash.update_tag();bpy.context.view_layer.update();save('a-native-seam-lash-bindings.json',bindings);deliver(0);dd,N,NT=u.b.geom(skin);assert np.array_equal(N,W) and np.array_equal(NT,TT);assert np.array_equal(originalUV,q.arr(raw.uv_layers['VitruvianUV.UDIM'].data,'uv',len(raw.loops),2));assert np.array_equal(q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']),H0);skin['AFN107_scope']='Original coarse native quad eyelid sculpt baked into actual full skin keys and half corrective; no SurfaceDeform input-key suppression. Authoring cage retained, not live-linked to baked keys. Native seam lash bindings preserve actual winding; anatomical margin and finite/continuous contacts unaccepted.';save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'newVisibleSkinKeys':4,'neutralHeadBodyAndR105UVExactlyRetained':True,'neutralFullGroomExactlyRetained':True,'all412LashesAndOriginalRadiiRetained':True,'nativeUVSeamBindingNotAnatomicalMarginProof':True,'lashRootPlacementChangeQuantilesM':np.quantile(errors,[0,.5,.95,1]),'actualSkinBodyModifiers':[(m.name,m.type) for m in skin.modifiers],'wholeBodyDeformationStillUnconnected':True,'secondsBeforePreview':time.time()-tick});u.m.m.rig.shade.settings();u.m.m.rig.k.b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','body-face']:views.append(u.v.image('a-coarse-lid-character',view));save('a-view-controls.json',views)
 motion=[]
 for tag,value in [('half',.5),('closed',1.),('restored',0.)]:
  deliver(value);dd,V,TV=u.b.geom(skin);motion.append({'state':tag,'assignedBlink':value,'evaluatedKeys':{k.name:k.value for k in raw.shape_keys.key_blocks if k.name!='Basis'},'maximumDisplayedSkinMoveM':float(np.linalg.norm(V-W,axis=1).max()),'actualTopologyUnchanged':bool(np.array_equal(TV,TT))});views.append(u.v.image('a-coarse-lid-character-'+tag,'face'));save('a-preview-motion.json',motion);save('a-view-controls.json',views)
 print('R107_COMPLETE_NATIVE_COARSE_CHARACTER_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
