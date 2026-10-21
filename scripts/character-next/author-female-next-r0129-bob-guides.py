"""Direct explicit3D bob strokes on the current artist woman's actual scalp."""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0129-native-authored-bob';PRE=E.parent/'r0127-native-lid-closure';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend';OUT=S/'r0129-source/aevrynd-female-next-r0129-a-native-bob-guide-authoring.blend'
sp=importlib.util.spec_from_file_location('r129guidesbase',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def smooth(P):
 P=np.array(P);out=[]
 for i in range(len(P)-1):
  p,q,r,s=P[max(i-1,0)],P[i],P[i+1],P[min(i+2,len(P)-1)]
  for t in np.linspace(0,1,12,endpoint=False):out.append(.5*((2*q)+(-p+r)*t+(2*p-5*q+4*r-s)*t*t+(-p+3*q-3*r+s)*t*t*t))
 return np.array(out+[P[-1]])
def sample(P,N):
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];return np.column_stack([np.interp(np.linspace(0,arc[-1],N),arc,P[:,j]) for j in range(3)])
def main():
 tick=time.time();assert not OUT.exists();save('bob-guide-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct Blender guide-mesh authoring from explicit frontal/temple/posterior bob strokes on actual current native scalp. Guide-only stage, not appearance adoption.'});bpy.ops.wm.open_mainfile(filepath=str(SRC));protected=a.protected();skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];_,W,BT=b.u.b.geom(skin);W=W.copy();BT=BT.copy();native=np.load(PRE/'native-head-topology.npz');P=native['world'];T=native['triangles'];domain=np.load(E/'authored-native-scalp-domain.npz');cap=domain['nativeScalpFaceIds'];verts=domain['nativeScalpVertexIds'];kt=KDTree(len(P))
 for i,p in enumerate(P):kt.insert(Vector(p),i)
 kt.balance();ids=np.full(len(W),-1,dtype=np.int32)
 for i in np.flatnonzero(W[:,2]>1.4):
  _,j,ds=kt.find(Vector(W[i]))
  if ds<5e-7:ids[i]=j
 lookup={tuple(sorted(t)):i for i,t in enumerate(T)};sourceToActual={}
 for i,f in enumerate(BT):
  m=ids[f]
  if m.min()>=0:
   n=lookup.get(tuple(sorted(m)))
   if n is not None:sourceToActual[n]=i
 assert all(int(i) in sourceToActual for i in cap)
 # Explicit artist strokes traced in actual current hair volume, not a scalp
 # radial/height growth formula. Separate side sweeps and posterior/nape lengths.
 front=[([.008,-.085,1.555],[[.028,-.100,1.582],[.063,-.105,1.571],[.100,-.091,1.540],[.115,-.080,1.490],[.100,-.091,1.450],[.122,-.070,1.408],[.102,-.047,1.365]]),([.006,-.055,1.570],[[.026,-.063,1.592],[.065,-.080,1.584],[.104,-.068,1.549],[.128,-.049,1.506],[.112,-.068,1.461],[.122,-.050,1.414],[.105,-.031,1.364]]),([.006,-.015,1.575],[[.025,-.015,1.595],[.066,-.027,1.581],[.107,-.015,1.545],[.130,.006,1.500],[.112,-.014,1.453],[.119,.010,1.405],[.099,.016,1.362]]),([.006,.025,1.565],[[.028,.035,1.588],[.069,.025,1.570],[.111,.040,1.526],[.124,.053,1.488],[.109,.035,1.449],[.118,.047,1.404],[.092,.038,1.368]]),([.042,-.065,1.555],[[.060,-.078,1.573],[.095,-.082,1.548],[.117,-.065,1.509],[.104,-.080,1.468],[.122,-.060,1.420],[.104,-.040,1.374]]),([.065,-.045,1.535],[[.080,-.050,1.552],[.112,-.047,1.523],[.124,-.028,1.484],[.111,-.045,1.443],[.122,-.022,1.397],[.097,-.015,1.354]]),([.075,-.005,1.515],[[.094,-.002,1.529],[.122,.015,1.490],[.110,.002,1.451],[.120,.025,1.412],[.097,.029,1.365]]),([.065,.025,1.530],[[.087,.042,1.541],[.116,.062,1.501],[.108,.045,1.459],[.118,.065,1.420],[.094,.058,1.370]])]
 strokes=[]
 for sign in [-1,1]:
  for j,(pick,path) in enumerate(front):
   Q=np.array(path,dtype=float);Q[:,0]*=sign
   if sign<0:Q[:,2]+=np.linspace(.001,-.004,len(Q));Q[:,1]+=np.linspace(-.001,.003,len(Q))
   strokes.append({'region':'L' if sign<0 else 'R','name':('L' if sign<0 else 'R')+'_sweep_'+str(j),'rootPick':[sign*pick[0],pick[1],pick[2]],'freeControlPoints':Q})
 for row,z in enumerate([1.553,1.510,1.460]):
  for column,x in enumerate([-.056,-.028,0,.028,.056]):
   pick=[x,.045 if row==0 else (.065 if row==1 else .055),z];y=.092 if row<2 else .082
   path=[[x*1.08,y-.015,z+.005],[x*1.18,y+.015,z-.028],[x*1.10,y,z-.063],[x*1.30,y+.012,max(1.375,z-.104)],[x*1.05,y-.015,1.355+.006*(column%2)]]
   strokes.append({'region':'B','name':'back_'+str(row)+'_'+str(column),'rootPick':pick,'freeControlPoints':np.array(path)})
 G=[];records=[]
 for si,s in enumerate(strokes):
  vi=int(verts[np.argmin(np.linalg.norm(P[verts]-s['rootPick'],axis=1))]);fi=next(int(f) for f in cap if vi in T[f]);actual=sourceToActual[fi];tri=BT[actual];co=int(np.where(ids[tri]==vi)[0][0]);weights=np.eye(3)[co];root=weights@W[tri];normal=np.cross(W[tri[1]]-W[tri[0]],W[tri[2]]-W[tri[0]]);normal/=np.linalg.norm(normal);start=root+normal*.000035;path=sample(smooth(np.r_[(start+normal*.0015)[None,:],s['freeControlPoints']]),40);g=np.r_[start[None,:],path];assert np.isfinite(g).all() and abs(g[:,0]).max()<.16 and g[:,2].max()<1.62 and g[:,2].min()>1.32;G.append(g);records.append({**s,'guide':si,'pickedNativeScalpVertex':vi,'nativeScalpTriangle':fi,'actualSkinTriangle':int(actual),'actualSkinVertexIds':tri,'rootBarycentric':weights,'actualRootSurfaceWorld':root,'actualRootNormal':normal})
 G=np.array(G);mesh=bpy.data.meshes.new('AFN129_EXPLICIT_41_POINT_BOB_GUIDES');mesh.from_pydata(G.reshape(-1,3).tolist(),[(i*41+j,i*41+j+1) for i in range(len(G)) for j in range(40)],[]);mesh.update();guide=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(guide);guide.hide_render=True;guide.display_type='WIRE';guide.show_in_front=True;guide['scope']='Explicit3D native bob artist strokes; actual surface-owned root picks and editable free guide points. Guide-only source stage, no complete appearance/natural dynamics/finite contact acceptance.';assert protected==a.protected();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);np.savez_compressed(E/'authored-native-guide-lineage.npz',guideWorld=G,actualSkinWorld=W,actualSkinTriangles=BT,nativeSourceToActualTriangle=np.array([[i,sourceToActual[int(i)]] for i in cap]),actualSkinNativePointIds=ids,guideNativeRootVertexIds=np.array([r['pickedNativeScalpVertex'] for r in records]));save('authored-native-bob-guides.json',records);save('a-build-summary.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(OUT),'sha256':a.sha(OUT),'bytes':OUT.stat().st_size,'guideObject':guide.name,'guides':len(G),'pointsEach':41,'actualSkinObject':skin.name,'protectedOldRollbackExact':protected==a.protected(),'guideOnlyStageNotAnAppearanceImprovement':True,'references':'Actual original Angelica3D hair silhouette and matched primary/profile/back views, author credit/license retained. No foreign emitter or procedural radial routes.','seconds':time.time()-tick});print('R129_NATIVE_COMPLETE_GUIDE_SOURCE_SAVED',len(G),time.time()-tick,flush=True)
if __name__=='__main__':main()
