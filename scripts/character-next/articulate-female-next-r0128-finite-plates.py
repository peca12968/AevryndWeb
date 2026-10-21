"""Articulate actual finite source-native tarsal plates and attached outer skin.
The plate is a separated finite layer with native outer UV; actual ocular
exterior defines its closed backing surface. A native boundary attachment
extends displacement into free skin, not the r127 single-rim angular warp.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,heapq,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0128-finite-native-lid-walls';PRE=E.parent/'r0127-native-lid-closure';SRC=S/'r0128-source/aevrynd-female-next-r0128-a-finite-native-plates.blend';OUT=S/'r0128-source/aevrynd-female-next-r0128-b-articulated-finite-plates.blend'
sp=importlib.util.spec_from_file_location('r128attach',Path(__file__).with_name('build-female-next-r0127-native-lid-closure.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def deliver(value):
 c=bpy.data.objects['AFN128_FINITE_LID_CONTROLS']
 for side in ['l','r']:c['blink_'+side]=value
 c.update_tag();bpy.context.view_layer.update()
def drive(ob,poses,controller):
 a.drive(ob,poses,controller)
 for key in ob.data.shape_keys.key_blocks:
  if key.name.startswith('AFN127_'):key.name=key.name.replace('AFN127_','AFN128_',1)
def main():
 tick=time.time();assert not OUT.exists();save('finite-plate-articulation-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct finite outer tarsal plate closure on original source ocular exterior, explicit inner wall/outer UV/rim material, native free-skin boundary connection and source lash/wetline attachments on same complete woman.'});bpy.ops.wm.open_mainfile(filepath=str(SRC));protected=a.a.protected();native=np.load(PRE/'native-head-topology.npz');P=native['world'];T=native['triangles'];dom=np.load(E/'authored-native-plate-domains.npz');sock=np.load(E/'actual-native-lid-domains.npz');k=a.tree(P);adj=[[] for p in P]
 for i,j in native['edges']:w=float(np.linalg.norm(P[i]-P[j]));adj[i].append((int(j),w));adj[j].append((int(i),w))
 controller=bpy.data.objects.new('AFN128_FINITE_LID_CONTROLS',None);bpy.context.scene.collection.objects.link(controller);controller.empty_display_type='PLAIN_AXES';controller.empty_display_size=.015;controller.location=(0,-.18,1.49)
 for side in ['l','r']:controller['blink_'+side]=0.;controller.id_properties_ui('blink_'+side).update(min=0,max=1,description='Actual displayed finite native lid, unaccepted anatomical/contact research.')
 eye=bpy.data.objects['AFN126_ORIGINAL_EyeScleraReflect_EyeScleraReflect_0'];_,EV,ET=b.u.b.geom(eye);EV=EV.copy();ET=ET.copy();eyeTree=BVHTree.FromPolygons(EV.tolist(),ET.tolist(),all_triangles=True,epsilon=0.);upper=[4760,5920,6065,6002,5993,5933,5982,5971,5960,6495];lower=[6106,10251,6182,6312,6319,6330,6338,6349,6361,6497];nativePoses={};summary={};poseArrays={}
 for side,sign in [('R',1),('L',-1)]:
  plateIds=np.unique(T[dom[side+'_plateFaces']]);plateP=P[plateIds];U=P[upper].copy();L=P[lower].copy();U[:,0]*=sign;L[:,0]*=sign;U=U[np.argsort(U[:,0])];L=L[np.argsort(L[:,0])];G=EV[(EV[:,0]*sign>0)&(EV[:,1]>-.109)];base=G.mean(0);g=G-base;fit=np.linalg.lstsq(np.c_[2*g,np.ones(len(g))],(g*g).sum(1),rcond=None)[0];center=base+fit[:3];dist=np.full(len(P),np.inf);owner=np.full(len(P),-1,dtype=np.int32);heap=[]
  for i in plateIds:dist[i]=0.;owner[i]=i;heapq.heappush(heap,(0.,int(i)))
  while heap:
   ds,i=heapq.heappop(heap)
   if ds!=dist[i] or ds>.012:continue
   for j,w in adj[i]:
    nd=ds+w
    if nd<dist[j] and nd<=.012:dist[j]=nd;owner[j]=owner[i];heapq.heappush(heap,(nd,j))
  affected=np.flatnonzero(np.isfinite(dist));fade=.5*(1+np.cos(np.pi*dist[affected]/.012));sourceU=np.column_stack([np.interp(plateP[:,0],U[:,0],U[:,q]) for q in range(3)]);sourceL=np.column_stack([np.interp(plateP[:,0],L[:,0],L[:,q]) for q in range(3)]);angleU=np.arctan2(sourceU[:,2]-center[2],center[1]-sourceU[:,1]);angleL=np.arctan2(sourceL[:,2]-center[2],center[1]-sourceL[:,1]);delta=angleL-angleU;lookup={int(j):i for i,j in enumerate(plateIds)};poseList=[];rayRows=[]
  for value in [.25,.5,1.]:
   d=plateP-center;ang=np.arctan2(d[:,2],-d[:,1])+value*delta;rad=np.linalg.norm(d[:,1:],axis=1);Q=plateP.copy();Q[:,1]=center[1]-rad*np.cos(ang);Q[:,2]=center[2]+rad*np.sin(ang)
   # Rigid meridian transport maps the actual upper edge onto the native lower
   # edge. Closed backing is reconstructed from original ocular triangles,
   # then the outer sheet carries the explicit0.5mm finite thickness.
   u=sourceU-center;ua=angleU+value*delta;ur=np.linalg.norm(u[:,1:],axis=1);uRot=np.c_[sourceU[:,0],center[1]-ur*np.cos(ua),center[2]+ur*np.sin(ua)];goal=(1-value)*sourceU+value*sourceL;Q+=goal-uRot;curved=Q.copy();hits=[]
   for i,pos in enumerate(Q):
    direction=(Vector(pos)-Vector(center)).normalized();hit,normal,face,distance=eyeTree.ray_cast(Vector(center),direction)
    assert hit is not None,('source native ocular exterior missing',side,int(plateIds[i]),value)
    no=np.array(normal);no*=1 if no@np.array(direction)>0 else -1;curved[i]=np.array(hit)+.0005*no;hits.append((int(face),float(distance)))
   Q=(1-value)*Q+value*curved;displacement=Q-plateP;A=P.copy();A[affected]+=np.array([displacement[lookup[int(owner[j])]] for j in affected])*fade[:,None];A[plateIds]=Q;assert np.isfinite(A).all();poseList.append(A);poseArrays[side+str(value)]=A;rayRows.append({'value':value,'sourceExteriorRayCount':len(hits),'rayHitTriangleIds':[x[0] for x in hits],'sourceThicknessM':.0005,'noFiniteClearanceOrContinuousProof':True})
  nativePoses[side]=poseList;summary[side]={'finiteNativePlateVertices':len(plateIds),'finiteNativePlateOuterTriangles':len(dom[side+'_plateFaces']),'sourcePosteriorFitPivot':center,'sourceRayBacking':rayRows,'freeSkinBoundarySupportGeodesicM':.012,'actualSourceOwnership':'Separate native outer tarsal plate, new inner wall and rolled margin. Free outer skin receives displacement at the actual plate boundary; blind source socket is removed/replaced, not stretched into the visible closure.'}
 # Build keys for actual remaining complete skin and both actual finite plates.
 for name in ['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD','AFN128_L_FINITE_TARSAL_PLATE','AFN128_R_FINITE_TARSAL_PLATE']:
  ob=bpy.data.objects[name];W=a.world(ob);ids=np.full(len(W),-1,dtype=np.int32)
  for i in np.flatnonzero(W[:,2]>1.4):
   _,j,ds=k.find(Vector(W[i]))
   if ds<5e-7:ids[i]=j
  poses={}
  for side in ['L','R']:
   poses[side]=[]
   for A in nativePoses[side]:
    Q=W.copy();valid=np.flatnonzero(ids>=0);Q[valid]+=A[ids[valid]]-P[ids[valid]];poses[side].append(Q)
  drive(ob,poses,controller)
  if 'FINITE_TARSAL_PLATE' in name:
   inner=bpy.data.materials.get('AFN128_INNER_LID_TISSUE_APPROXIMATION')
   if inner is None:
    inner=bpy.data.materials.new('AFN128_INNER_LID_TISSUE_APPROXIMATION');inner.use_nodes=True;node=next(n for n in inner.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');node.inputs['Base Color'].default_value=(.24,.065,.05,1.);node.inputs['Roughness'].default_value=.42
   ob.data.materials.append(inner);ob.modifiers[0].material_offset=1;ob.modifiers[0].material_offset_rim=1
 # Native lash/wetline attachment is recomputed on actual retained exterior,
 # excluding the replaced blind socket surface. Neutral source offsets remain.
 excluded=set(np.r_[sock['L_socketFaces'],sock['R_socketFaces']]);outerT=T[[i for i in range(len(T)) if i not in excluded]];bt=BVHTree.FromPolygons(P.tolist(),outerT.tolist(),all_triangles=True);parts={}
 for name in ['AFN126_ORIGINAL_Eyelashes_Eyelashes_0','AFN126_ORIGINAL_MeniscusEyeSpec_MeniscusEye_0']:
  ob=bpy.data.objects[name];W=a.world(ob);groups=a.components(ob) if 'Eyelashes' in name else [[i] for i in range(len(W))];bound=[]
  for ids in groups:
   root=W[ids[np.argmax(W[ids,1])]] if len(ids)>1 else W[ids[0]];nearest,normal,fi,ds=bt.find_nearest(Vector(root));tri=outerT[fi];A=P[tri];bary=np.linalg.lstsq(np.r_[A.T,np.ones((1,3))],np.r_[np.array(nearest),1.],rcond=None)[0];bound.append((ids,tri,bary,a.frame(A),A.T@bary,float(ds)))
  poses={};inv=np.array(ob.matrix_world.inverted())
  for side in ['L','R']:
   poses[side]=[]
   for A in nativePoses[side]:
    N=W.copy()
    for ids,tri,bary,F,root,ds in bound:new=A[tri];rot=a.frame(new)@F.T;N[ids]=(W[ids]-root)@rot.T+new.T@bary
    poses[side].append(N@inv[:3,:3].T+inv[:3,3])
  drive(ob,poses,controller);parts[name]={'actualSourceGroups':len(groups),'actualRetainedExteriorTriangleAttachments':len(bound),'neutralRootDistanceRangeM':[min(x[-1] for x in bound),max(x[-1] for x in bound)],'rawSourceDistanceNotFiniteContactProof':True}
 deliver(0.);assert protected==a.a.protected();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);np.savez_compressed(E/'finite-lid-articulation-lineage.npz',sourceHead=P,sourceTriangles=T,**poseArrays)
 save('b-build-summary.json',{'source':str(SRC),'sourceSha256':a.a.sha(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkinObject':'AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD','actualControl':'AFN128_FINITE_LID_CONTROLS','actualFinitePlateObjects':['AFN128_L_FINITE_TARSAL_PLATE','AFN128_R_FINITE_TARSAL_PLATE'],'nativeAnatomicalConstruction':summary,'actualLashWetlineAttachments':parts,'oldHiddenRollbackExact':protected==a.a.protected(),'appearanceFunctionFiniteContactRuntimeUnacceptedBeforeReview':True,'explicitSourceThicknessIsApproximateNotBiologicalCalibration':True,'secondsBeforePreview':time.time()-tick})
 rows=[]
 # Complete head/body and affected motion first, before other neutral angles.
 for view in ['face','body-face']:rows.append(b.u.v.image('b-finite-lids',view));save('b-view-controls.json',rows)
 for label,value in [('quarter',.25),('half',.5),('closed',1.),('restored',0.)]:deliver(value);rows.append(b.u.v.image('b-finite-lids-'+label,'face'));save('b-view-controls.json',rows)
 for view in ['profile','oblique','back']:rows.append(b.u.v.image('b-finite-lids',view));save('b-view-controls.json',rows)
 deliver(1.);rows.append(b.u.v.image('b-finite-lids-closed','oblique'));save('b-view-controls.json',rows);deliver(0.);print('R128_COMPLETE_FINITE_LID_AND_MOTION_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
