"""Author source-native upper-lid articulation on the actual complete r126 woman.
Native semantic rim chains, source socket geodesics and actual source globe pivot;
no foreign pose transfer, aperture ellipse or nearest head-envelope projection.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,heapq,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0127-native-lid-closure';SRC=S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend';OUT=S/'r0127-source/aevrynd-female-next-r0127-a-native-lid-articulation.blend'
sp=importlib.util.spec_from_file_location('r127base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,d):(E/n).write_text(json.dumps(d,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8')
def world(ob):return np.array([ob.matrix_world@v.co for v in ob.data.vertices],dtype=float)
def tree(P):
 k=KDTree(len(P))
 for i,p in enumerate(P):k.insert(Vector(p),i)
 k.balance();return k
def path(adj,start,end):
 ds={start:0.};prev={};heap=[(0.,start)]
 while heap:
  d,i=heapq.heappop(heap)
  if d!=ds[i]:continue
  if i==end:break
  for j,w in adj[i]:
   nd=d+w
   if nd<ds.get(j,float('inf')):ds[j]=nd;prev[j]=i;heapq.heappush(heap,(nd,j))
 out=[end]
 while out[-1]!=start:out.append(prev[out[-1]])
 return out[::-1]
def frame(P):
 x=P[1]-P[0];x/=np.linalg.norm(x);z=np.cross(x,P[2]-P[0]);z/=np.linalg.norm(z);return np.column_stack([x,np.cross(z,x),z])
def components(ob):
 adj=[[] for _ in ob.data.vertices]
 for e in ob.data.edges:i,j=e.vertices;adj[i].append(j);adj[j].append(i)
 unseen=set(range(len(adj)));out=[]
 while unseen:
  seed=next(iter(unseen));comp={seed};stack=[seed]
  while stack:
   for j in adj[stack.pop()]:
    if j not in comp:comp.add(j);stack.append(j)
  unseen-=comp;out.append(sorted(comp))
 return out
def drive(ob,poses,control):
 assert ob.data.shape_keys is None,ob.name
 ob.shape_key_add(name='Basis',from_mix=False)
 for side in ['L','R']:
  for index,label in enumerate(['Quarter','Half','Closed']):
   key=ob.shape_key_add(name='AFN127_'+side+'_'+label,from_mix=False);key.data.foreach_set('co',poses[side][index].astype(np.float32).ravel());fc=key.driver_add('value');d=fc.driver;d.type='SCRIPTED';v=d.variables.new();v.name='v';v.type='SINGLE_PROP';v.targets[0].id=control;v.targets[0].data_path='["blink_'+side.lower()+'"]';d.expression=['max(0,min(v/0.25,(0.5-v)/0.25))','max(0,min((v-0.25)/0.25,(1-v)/0.5))','max(0,min(1,(v-0.5)/0.5))'][index]
def deliver(value):
 ob=bpy.data.objects['AFN127_NATIVE_FACE_CONTROLS']
 for side in ['l','r']:ob['blink_'+side]=value
 ob.update_tag();bpy.context.view_layer.update()
def main():
 tick=time.time();assert not OUT.exists();save('native-lid-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct native rim-chain driven authored closure on displayed complete r126 woman; original neutral exact, no old hidden control substitution.'});bpy.ops.wm.open_mainfile(filepath=str(SRC));protected=a.protected();skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];W=world(skin);data=np.load(E/'native-head-topology.npz');P=data['world'];T=data['triangles'];edges=data['edges'];adj=[[] for p in P]
 for i,j in edges:w=float(np.linalg.norm(P[i]-P[j]));adj[i].append((j,w));adj[j].append((i,w))
 # Authored actual native vertices selected from the inspected sagittal section
 # and front source topology, following the innermost rolled upper/lower margins.
 upper=[4760,5920,6065,6002,5993,5933,5982,5971,5960,6495]
 lower=[6106,10251,6182,6312,6319,6330,6338,6349,6361,6497]
 # Corresponding native corners are joined via source edges, not generated ellipse.
 rim=[]
 for i,j in zip(upper,upper[1:]):rim+=path(adj,i,j)[:-1]
 rim.append(upper[-1]);rim=list(dict.fromkeys(rim));K=tree(P);skinNative=np.full(len(W),-1,dtype=np.int32);mappedDistances=[]
 for i in np.flatnonzero(W[:,2]>1.40):
  _,j,d=K.find(Vector(W[i]))
  if d<5e-7:skinNative[i]=j;mappedDistances.append(d)
 control=bpy.data.objects.new('AFN127_NATIVE_FACE_CONTROLS',None);bpy.context.scene.collection.objects.link(control);control.empty_display_type='PLAIN_AXES';control.empty_display_size=.015;control.location=(0,-.18,1.49)
 for side in ['l','r']:control['blink_'+side]=0.;control.id_properties_ui('blink_'+side).update(min=0,max=1,description='Native current visible artist head upper-lid closure. Research, contacts and visual review not accepted.')
 skinPoses={};nativePoses={};summaries={};allRim=[]
 for side,sign in [('R',1),('L',-1)]:
  ids=np.array(rim,dtype=np.int32) if sign==1 else np.array([K.find(Vector([-P[i,0],P[i,1],P[i,2]]))[1] for i in rim]);U=P[ids];L=P[lower].copy();L[:,0]*=sign;sort=np.argsort(L[:,0]);L=L[sort];Uorder=U[np.argsort(U[:,0])];globe=np.load(E/'EyeScleraReflect_EyeScleraReflect_0-native.npz')['world'];globe=globe[(globe[:,0]*sign>0)&(globe[:,1]>-.109)];base=globe.mean(0);g=globe-base;fit=np.linalg.lstsq(np.c_[2*g,np.ones(len(g))],(g*g).sum(1),rcond=None)[0];center=base+fit[:3];radius=float(np.sqrt(fit[3]+sum(fit[:3]**2)));residual=np.linalg.norm(globe-center,axis=1)-radius
  # Geodesic native-skin support, with complete rim vertices constrained equally.
  dist=np.full(len(P),np.inf);owner=np.full(len(P),-1,dtype=np.int32);heap=[]
  for j in ids:dist[j]=0;owner[j]=j;heapq.heappush(heap,(0.,int(j)))
  while heap:
   ds,i=heapq.heappop(heap)
   if ds!=dist[i] or ds>.012:continue
   for j,w in adj[i]:
    nd=ds+w
    if nd<dist[j] and nd<=.012:dist[j]=nd;owner[j]=owner[i];heapq.heappush(heap,(nd,j))
  affected=np.flatnonzero(np.isfinite(dist));seed=P[owner[affected]];lo=np.column_stack([np.interp(seed[:,0],L[:,0],L[:,k]) for k in range(3)]);theta=np.arctan2(seed[:,2]-center[2],center[1]-seed[:,1]);target=np.arctan2(lo[:,2]-center[2],center[1]-lo[:,1]);delta=target-theta;fade=.5*(1+np.cos(np.pi*dist[affected]/.012));delta*=fade
  sourceRad=np.linalg.norm(seed[:,1:]-center[1:],axis=1);lowerRad=np.linalg.norm(lo[:,1:]-center[1:],axis=1);radialDelta=(lowerRad-sourceRad)*fade
  pp=[];nn=[]
  for v in [.25,.5,1.]:
   A=P.copy();d=P[affected]-center;ang=np.arctan2(d[:,2],-d[:,1])+v*delta;rad=np.linalg.norm(d[:,1:],axis=1)+v*radialDelta;A[affected,1]=center[1]-rad*np.cos(ang);A[affected,2]=center[2]+rad*np.sin(ang);N=W.copy();valid=np.flatnonzero(skinNative>=0);N[valid]+=A[skinNative[valid]]-P[skinNative[valid]];assert np.isfinite(N).all();pp.append(N);nn.append(A)
  skinPoses[side]=pp;nativePoses[side]=nn;allRim.extend(ids);summaries[side]={'upperRimIds':ids,'upperRimWorld':U,'lowerAuthoredLandmarkWorld':L,'nativeGlobePosteriorFitCenter':center,'fitRadiusM':radius,'fitResidualRangeM':[residual.min(),residual.max()],'pivotFitOnlyNotContactOrSphereAnatomyProof':True,'supportGeodesicM':.012,'affectedNativeVertices':len(affected),'sourceRimRotationRangeRadians':[delta.min(),delta.max()],'maxNativeSkinMovementM':np.linalg.norm(nn[-1]-P,axis=1).max()}
 drive(skin,skinPoses,control)
 # Each original artist lash island retains its geometry in a moving native
 # surface frame attached to its actual source root; no independent gap offsets.
 bv=BVHTree.FromPolygons([Vector(p) for p in P],T.tolist(),all_triangles=True);attachments=[];partData={}
 for name in ['AFN126_ORIGINAL_Eyelashes_Eyelashes_0','AFN126_ORIGINAL_MeniscusEyeSpec_MeniscusEye_0']:
  ob=bpy.data.objects[name];B=world(ob);groups=components(ob) if 'Eyelashes' in name else [[i] for i in range(len(B))];bound=[]
  for ids in groups:
   root=B[ids[np.argmax(B[ids,1])]] if len(ids)>1 else B[ids[0]];nearest,normal,fi,dd=bv.find_nearest(Vector(root));tri=T[fi];A=P[tri];bary=np.linalg.lstsq(np.r_[A.T,np.ones((1,3))],np.r_[np.array(nearest),1.],rcond=None)[0];bound.append((ids,tri,bary,frame(A),A.T@bary,float(dd)))
  poses={};localInv=np.array(ob.matrix_world.inverted())
  for side in ['L','R']:
   poses[side]=[]
   for A in nativePoses[side]:
    C=B.copy()
    for ids,tri,bary,F,root,dd in bound:
     N=A[tri];rot=frame(N)@F.T;C[ids]=(B[ids]-root)@rot.T+N.T@bary
    poses[side].append(C@localInv[:3,:3].T+localInv[:3,3])
  drive(ob,poses,control);partData[name]={'originalIslands':len(groups),'nativeAttachments':len(bound),'rootNearestSkinDistanceRangeM':[min(x[-1] for x in bound),max(x[-1] for x in bound)],'sourceDistancePreservedInLocalFrameNotFiniteContactProof':True};attachments.append((name,[(ids,tri,bary,root) for ids,tri,bary,F,root,dd in bound]))
 deliver(0.);assert protected==a.protected();_,actual,tri=b.u.b.geom(skin);assert np.max(abs(actual-W))<2e-7
 skin['AFN127_scope']='Original r126 neutral exact. Source-native upper-lid rotation through3 editable authored poses; native lash/wetline attachment, own independent controls. Research pending visual/contact/independent readback; not old hidden rig.'
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 np.savez_compressed(E/'native-lid-authoring-lineage.npz',sourceHead=P,sourceTriangles=T,actualNeutral=W,actualNativeCorrespondence=skinNative,authoredUpperLandmarks=upper,authoredLowerLandmarks=lower,authoredRimIds=np.array(allRim),**{side+str(i):v for side in ['L','R'] for i,v in enumerate(nativePoses[side])})
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(OUT),'sha256':a.sha(OUT),'bytes':OUT.stat().st_size,'actualDisplayedSkin':skin.name,'actualNewControls':control.name,'allOldProtectedRollbackExact':protected==a.protected(),'sourceHeadMappingMaxM':max(mappedDistances),'actualNeutralPreservedMaxM':float(np.max(abs(actual-W))),'nativeRimsAndGlobe':summaries,'nativeAttachments':partData,'actualSkinVertices':len(W),'actualTriangles':len(tri),'fullFunctionFiniteContinuousContactRuntimeNotAccepted':True,'secondsBeforePreview':time.time()-tick,'methodChangedPremise':'Current artist native dense rolled lid and closed socket wall, coherent original eye/lash assembly measured from actual mesh, not old foreign-pose/envelope/aperture fields. Actual semantic source rim-edge paths constrained and geodesic support; no source mesh replacement or neutral shape warp.','references':[{'url':'https://pubmed.ncbi.nlm.nih.gov/7369314/','use':'Observed upper-lid predominant descent/lower mostly nasal movement; our lower lid remains at rest, timing/globe pressure not calibrated.'},{'url':'https://docs.blender.org/manual/en/5.0/animation/shape_keys/introduction.html','use':'Relative editable pose representation; offline normal Blender drivers, no addon/runtime dependency.'}]})
 rows=[]
 for view in ['face','body-face','profile','oblique','back']:rows.append(b.u.v.image('a-native-lid',view));save('a-view-controls.json',rows)
 for label,value in [('quarter',.25),('half',.5),('closed',1.),('restored',0.)]:deliver(value);rows.append(b.u.v.image('a-native-lid-'+label,'face'));save('a-view-controls.json',rows)
 print('R127_COMPLETE_NATIVE_LID_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
