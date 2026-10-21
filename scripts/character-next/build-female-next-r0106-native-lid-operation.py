"""Articulate existing native lid topology and reconnect the complete skin.

This preserves the artist head, r105 lip chart and original full groom. The
posterior socket is not filled/projected over the eye. Pose construction alone
is not a finite triangle/contact or natural blink certificate.
"""
from pathlib import Path
from collections import Counter,defaultdict
import bpy,numpy as np,json,time,datetime,heapq,math,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0106-native-head-operation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0105-a-native-lip-chart.blend';OUT=S/'aevrynd-female-next-r0106-a-native-lid-operation.blend'
sp=importlib.util.spec_from_file_location('r106shared',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def dist(P,adj,seeds):
 d=np.full(len(P),np.inf);heap=[]
 for i in seeds:d[i]=0;heapq.heappush(heap,(0,int(i)))
 while heap:
  value,i=heapq.heappop(heap)
  if value!=d[i] or value>.016:continue
  for j in adj[i]:
   nv=value+float(np.linalg.norm(P[j]-P[i]))
   if nv<d[j]:d[j]=nv;heapq.heappush(heap,(nv,j))
 return d
def deliver(value):
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];face['blink_left']=face['blink_right']=value;face.update_tag();skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];skin.data.shape_keys.update_tag();skin.update_tag();bpy.context.view_layer.update()
def main():
 tick=time.time();assert not OUT.exists();save('authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'construction':'Original native external lid seam articulation, posterior socket retained, full skin body-control rebind.','notContactCertification':True});ref=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');chart=np.load(E.parent/'r0105-native-head-skin-chart/actual-lip-and-native-chart.npz');P=ref['world'].copy();T=ref['triangles'];UV=chart['nativeUV-UVMap'];front=np.all((UV[:,:,1]>.5)&(UV[:,:,0]>.2)&(UV[:,:,0]<.8),axis=1);external=np.zeros(len(P),bool);external[np.unique(T[front])]=True;optical=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text())['eyes'];centres=np.array([optical[s]['posteriorSphereFitCentreWorld'] for s in ['L','R']]);centre=centres.mean(0);P=(P-centre)*(np.linalg.norm(centres[0]-centres[1])/.060)+centre;edges=[];adj=[set() for _ in P]
 for fi,tri in enumerate(T):
  for j,k in [(0,1),(1,2),(2,0)]:
   x,y=int(tri[j]),int(tri[k]);adj[x].add(y);adj[y].add(x)
   if front[fi]:edges.append((tuple(sorted((x,y))),fi,j,k))
 count=Counter(e[0] for e in edges);eyeEdges={};poses={};reports={};bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];freeze=bpy.data.objects['AFN101_LEGACY_SKIN_NEUTRAL_BLINK_INPUT'];legacy=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];routes=0
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 face['blink_left']=face['blink_right']=0.;oral['jaw_open']=0.;freeze['blink_left']=freeze['blink_right']=0.
 for fc in legacy.data.shape_keys.animation_data.drivers:
  for var in fc.driver.variables:
   for target in var.targets:
    if target.id==face and 'blink_' in target.data_path:target.id=freeze;routes+=1
 legacy.data.shape_keys.update_tag();legacy.update_tag();face.update_tag();oral.update_tag();bpy.context.view_layer.update();d,W,BT=u.b.geom(skin);W=W.copy();BT=BT.copy();H0=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).copy();raw=skin.data;hf=q.arr(raw.attributes['AFN104_SourceHeadFace'].data,'value',len(raw.polygons),dtype='i4');starts=q.arr(raw.polygons,'loop_start',len(raw.polygons),dtype='i4');counts=q.arr(raw.polygons,'loop_total',len(raw.polygons),dtype='i4');ids=q.arr(raw.loops,'vertex_index',len(raw.loops),dtype='i4');A=np.array(skin.matrix_world);AI=np.linalg.inv(A[:3,:3]);base=q.arr(raw.vertices,'co',len(raw.vertices),3);world=base@A[:3,:3].T+A[:3,3];headFaces=np.flatnonzero(hf>=0);headPointIDs=np.unique(np.concatenate([ids[starts[f]:starts[f]+counts[f]] for f in headFaces]));kd=KDTree(len(headPointIDs))
 for i in headPointIDs:kd.insert(Vector(world[i]),int(i))
 kd.balance();marginBody={};nativeToBodyFace={int(hf[f]):int(f) for f in headFaces}
 for side,sign in [('L',1),('R',-1)]:
  selected=[];loopAdj=defaultdict(list)
  for key,fi,j,k in edges:
   pp=P[list(key)]
   if count[key]==1 and np.all((pp[:,2]>1.44)&(pp[:,2]<1.485)&(pp[:,0]*sign>.008)&(pp[:,0]*sign<.055)&(pp[:,1]<-.10)):
    selected.append((key,fi));loopAdj[key[0]].append(key[1]);loopAdj[key[1]].append(key[0])
  assert len(loopAdj)==40 and all(len(x)==2 for x in loopAdj.values());lo=min(loopAdj,key=lambda i:P[i,0]);hi=max(loopAdj,key=lambda i:P[i,0]);arcs=[]
  for first in loopAdj[lo]:
   path=[lo,first]
   while path[-1]!=hi:
    nxt=[i for i in loopAdj[path[-1]] if i!=path[-2]];assert len(nxt)==1 and nxt[0] not in path;path.append(nxt[0])
   arcs.append(P[np.array(path)[np.argsort(P[path,0])]])
  upper=max(arcs,key=lambda x:x[:,2].mean());lower=min(arcs,key=lambda x:x[:,2].mean());_,EV,ET=u.b.geom(bpy.data.objects['AFN104_NATIVE_'+side+'_SCLERA']);EV=EV.copy();ET=ET.copy();c=(EV.min(0)+EV.max(0))/2;tree=BVHTree.FromPolygons(EV.tolist(),ET.tolist(),all_triangles=True);distance=dist(P,adj,loopAdj);radius=np.where(external,.014,.004);weight=np.clip(1-distance/radius,0,1);weight=weight*weight*(3-2*weight);change=np.zeros_like(P);hitCount=0
  for i in np.flatnonzero(weight>0):
   x=P[i,0];up=np.array([np.interp(x,upper[:,0],upper[:,j]) for j in range(3)]);low=np.array([np.interp(x,lower[:,0],lower[:,j]) for j in range(3)]);seam=.25*up+.75*low;isUpper=P[i,2]>=(up[2]+low[2])/2;margin=up if isUpper else low;hit,no,fi,dis=tree.ray_cast(Vector((x,EV[:,1].min()-.02,seam[2])),Vector((0,1,0)))
   if hit is None:continue
   hitCount+=1;target=np.array([x,hit.y-.0004,seam[2]]);oldAngle=np.arctan2(margin[2]-c[2],c[1]-margin[1]);targetAngle=np.arctan2(target[2]-c[2],c[1]-target[1]);angle=np.arctan2(P[i,2]-c[2],c[1]-P[i,1])+(targetAngle-oldAngle)*weight[i];rho=np.linalg.norm(P[i,1:]-c[1:]);marginR=np.linalg.norm(margin[1:]-c[1:]);targetR=np.linalg.norm(target[1:]-c[1:]);rho+=(targetR-marginR)*weight[i];change[i]=np.array([x,c[1]-rho*np.cos(angle),c[2]+rho*np.sin(angle)])-P[i]
  poses[side]=change;eyeEdges[side]=selected
  for i in loopAdj:
   _,bodyID,error=kd.find(Vector(P[i]));assert error<3e-6,error;marginBody[i]=bodyID
  reports[side]={'nativeExternalMarginVertices':list(loopAdj),'nativeUpperArcWorld':upper,'nativeLowerArcWorld':lower,'actualSourceFrontFacesUsed':True,'movedNativeVertices':int(np.count_nonzero(np.linalg.norm(change,axis=1)>1e-12)),'maximumSourceMoveM':float(np.linalg.norm(change,axis=1).max()),'outerLidInfluenceGeodesicM':.014,'shortInnerWallInfluenceGeodesicM':.004,'posteriorSocketOutsideInfluenceRetained':True,'actualOpticalRayHits':hitCount,'authoredMarginFrontClearanceM':.0004,'clearanceIsConstructionNotTriangleProof':True}
 skin.shape_key_add(name='Basis');keyDeltas={s:np.zeros_like(world) for s in poses}
 for f in headFaces:
  fi=hf[f];loops=ids[starts[f]:starts[f]+counts[f]];tri=P[T[fi]];M=np.column_stack((tri[1]-tri[0],tri[2]-tri[0]));xy=np.linalg.lstsq(M,(world[loops]-tri[0]).T,rcond=None)[0].T;bary=np.c_[1-xy.sum(1),xy]
  for side in poses:keyDeltas[side][loops]=bary@poses[side][T[fi]]
 for side,prop in [('L','blink_left'),('R','blink_right')]:
  key=skin.shape_key_add(name='AFN106_NATIVE_BLINK_'+side);key.data.foreach_set('co',(base+keyDeltas[side]@AI.T).astype('f4').ravel());fc=key.driver_add('value');fc.driver.expression='v';var=fc.driver.variables.new();var.name='v';var.type='SINGLE_PROP';var.targets[0].id=face;var.targets[0].data_path='["'+prop+'"]'
 # New topology must be bound afresh; never copy a bound SurfaceDeform modifier.
 cage=bpy.data.objects['AFN99_FULL_ORIGINAL_CONTROL_CAGE'];md=skin.modifiers.new('AFN106_COMPLETE_SKIN_ORIGINAL_BODY_CONTROL','SURFACE_DEFORM');md.target=cage
 for ob in bpy.context.selected_objects:ob.select_set(False)
 skin.hide_set(False);skin.select_set(True);bpy.context.view_layer.objects.active=skin;bpy.context.view_layer.update();save('prebind-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'nativeLidsAuthored':reports,'legacyBlinkRoutesFrozen':routes});bpy.ops.object.surfacedeform_bind(modifier=md.name);assert md.is_bound;bpy.context.view_layer.update();_,bound,_=u.b.geom(skin);correction=(W-bound)@AI.T;rest=float(np.linalg.norm(bound-W,axis=1).max());assert rest<.001,rest;raw.attributes.new('AFN106_BindRestCorrection','FLOAT_VECTOR','POINT').data.foreach_set('vector',correction.astype('f4').ravel());ng,n,L=u.m.interface('AFN106_EXPLICIT_NEUTRAL_BIND_CORRECTION');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');attr=n.new('GeometryNodeInputNamedAttribute');attr.data_type='FLOAT_VECTOR';attr.inputs['Name'].default_value='AFN106_BindRestCorrection';setpos=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(attr.outputs['Attribute'],setpos.inputs['Offset']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);skin.modifiers.new('AFN106_NEUTRAL_BIND_CORRECTION','NODES').node_group=ng
 # Reattach every original lash to an actual native external margin edge.
 lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];LH=q.geom(lash)[1].copy();LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);VL=(W-LA[:3,3])@LI.T;bindings=json.loads((E.parent/'r0104-native-artist-ocular-foundation/b-retained-lash-bindings.json').read_text());lids=np.empty((len(LH),3),'i4');weights=np.empty_like(LH);offset=np.empty_like(LH);errors=[]
 for row in bindings:
  start=row['pointStart'];end=start+row['points'];point=LH[start];side='L' if point[0]>0 else 'R';best=None
  for (a,b),fi in eyeEdges[side]:
   pa,pb=P[a],P[b];t=float(np.clip(np.dot(point-pa,pb-pa)/np.dot(pb-pa,pb-pa),0,1));hit=pa+t*(pb-pa);error=float(np.linalg.norm(point-hit))
   if best is None or error<best[0]:best=(error,a,b,fi,t)
  error,a,b,fi,t=best;f=nativeToBodyFace[fi];tri=list(ids[starts[f]:starts[f]+counts[f]]);aa,bb=marginBody[a],marginBody[b];third=next(i for i in tri if i not in [aa,bb]);tri=[aa,bb,third];p=VL[tri];tangent=p[1]-p[0];tangent/=np.linalg.norm(tangent);normal=np.cross(p[1]-p[0],p[2]-p[0]);normal/=np.linalg.norm(normal);frame=np.column_stack((tangent,np.cross(normal,tangent),normal));lids[start:end]=tri;weights[start:end]=[1-t,t,0];offset[start:end]=((LH[start:end]-LH[start])@LI.T)@frame;errors.append(error);row.update({'actualNativeMarginEdge':[int(a),int(b)],'actualSkinTriangle':tri,'barycentric':[1-t,t,0],'neutralRootPlacementChangeM':error,'anatomicalSourceMarginEdgeUsed':True,'finiteFollicleOrShaftContactAccepted':False})
 for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',lids[:,j])
 lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',weights.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());lash.data.update_tag();lash.update_tag();bpy.context.view_layer.update();save('a-lash-native-margin-bindings.json',bindings);_,neutral,NT=u.b.geom(skin);neutral=neutral.copy();assert np.linalg.norm(neutral-W,axis=1).max()<4e-6;hairError=float(np.linalg.norm(q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'])-H0,axis=1).max());assert hairError<6e-6
 save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'nativeLids':reports,'legacyBlinkRoutesFrozen':routes,'surfaceDeformFreshlyBound':md.is_bound,'uncompensatedNeutralBindResidueM':rest,'neutralWorldMaximumChangeM':float(np.linalg.norm(neutral-W,axis=1).max()),'neutralGroomMaximumWorldChangeM':hairError,'allOriginal412LashesRetained':True,'lashRootPlacementChangeQuantilesM':np.quantile(errors,[0,.5,.95,1]),'sourceHeadShapeAndR105UVPreservedAtNeutral':True,'completeOperationAppearanceContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick});skin['AFN106_scope']='Original native eye seam articulation and fresh complete body-control binding. Source art and lip chart retained. All412 lashes on original native outer lid edges. Preview first; finite/continuous contacts, natural blink/hair, complete operation and runtime unaccepted.';u.m.m.rig.shade.settings();u.m.m.rig.k.b.camera('face');scene.camera.data.lens=85;scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;deliver(0);bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','body-face']:views.append(u.v.image('a-native-lid-operation',view));save('a-view-controls.json',views)
 motions=[]
 for tag,value in [('half',.5),('closed',1.),('restored',0.)]:
  deliver(value);dd,V,TT=u.b.geom(skin);motions.append({'state':tag,'assignedBlink':value,'evaluatedOwnKeys':[skin.data.shape_keys.key_blocks['AFN106_NATIVE_BLINK_'+s].value for s in ['L','R']],'maximumDisplayedSkinMoveM':float(np.linalg.norm(V-neutral,axis=1).max()),'actualTopologyRetained':bool(np.array_equal(TT,NT))});views.append(u.v.image('a-native-lid-operation-'+tag,'face'));save('a-preview-motion.json',motions);save('a-view-controls.json',views)
 print('R106_COMPLETE_WOMAN_AND_NATIVE_BLINK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
