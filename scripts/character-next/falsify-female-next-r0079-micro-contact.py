"""Bounded closest-parameter common-interior micro-shaft falsification."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0079-physical-filaments'
old=Path(__file__).with_name('falsify-female-next-r0079-same-parameter.py').read_text(encoding='utf-8-sig');exec(compile(old.split("ref=q.read(E/'b-original-frame-build-summary.json')")[0],str(__file__),'exec'))
def evaluate(x,t):
 a,b,c,d=x;z=-a+3*b-3*c+d;w=2*a-5*b+4*c-d;v=-a+c
 return .5*(2*b+v*t+w*t*t+z*t**3),.5*(v+2*w*t+3*z*t*t),w+3*z*t

def closest(x,y,u,v):
 for _ in range(40):
  pa,ta,aa=evaluate(x,u);pb,tb,bb=evaluate(y,v);delta=pa-pb;g=np.array((delta@ta,-delta@tb));h=np.array(((ta@ta+delta@aa,-ta@tb),(-ta@tb,tb@tb-delta@bb)));ev=np.linalg.eigvalsh(h);h+=np.eye(2)*max(0.,1e-12-ev[0]);step=np.linalg.solve(h,-g);step=np.clip(step,-.25,.25);base=delta@delta;accepted=False
  for k in range(12):
   uv=np.clip(np.array((u,v))+step*(.5**k),1e-8,1-1e-8);da=evaluate(x,uv[0])[0]-evaluate(y,uv[1])[0]
   if da@da<base:u,v=map(float,uv);accepted=True;break
  if not accepted or np.linalg.norm(step)<1e-12:break
 return u,v

tick=time.time();ref=q.read(E/'b-original-frame-build-summary.json');assert hashlib.sha256(Path(ref['output']).read_bytes()).hexdigest()==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=q.arr(d.position_data,'vector',len(d.position_data),3).astype('f8');rr=q.arr(d.attributes['radius'].data,'value',len(P)).astype('f8');A=np.array(o.matrix_world);sv=np.linalg.svd(A[:3,:3],compute_uv=False);z=np.load(E/'b-AFN68_MAIN_RENDER_CURVES-physical-lineage.npz');counts=z['counts'];starts=np.r_[0,np.cumsum(counts)[:-1]];candidates=[]
for n in np.unique(counts):
 ids=np.flatnonzero(counts==n);ix=starts[ids,None,None]*3+np.arange(3)[None,:,None]*n+np.arange(n)[None,None,:];x=P[ix];r=rr[ix];a=np.concatenate((x[:,:,:1],x[:,:,:-1]),2)[:,:,:-1];b=x[:,:,:-1];c=x[:,:,1:];dd=np.concatenate((x[:,:,1:],x[:,:,-1:]),2)[:,:,1:];limit=int(n)-4
 for t in (.25,.5,.75):
  value=.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-dd)*t*t+(-a+3*b-3*c+dd)*t**3)
  for ca,cb in ((0,1),(0,2),(1,2)):
   dist=np.linalg.norm(value[:,ca,:limit]-value[:,cb,:limit],axis=2);ratio=dist/(r[:,ca,:limit]+r[:,cb,:limit]);number=min(24,ratio.size);which=np.argpartition(ratio.ravel(),number-1)[:number]
   for flat in which:ii,seg=np.unravel_index(flat,ratio.shape);candidates.append((float(ratio[ii,seg]),int(ids[ii]),int(n),int(seg),t,ca,cb))
candidates.sort();found=[];tested=0
for ratio,ci,n,seg,t,ca,cb in candidates[:128]:
 idx=[max(0,seg-1),seg,seg+1,min(n-1,seg+2)];base=int(starts[ci])*3;xa=P[base+ca*n+np.array(idx)];xb=P[base+cb*n+np.array(idx)];r=[]
 for child in (ca,cb):
  rho=rr[base+child*n+np.array(idx)];bc=np.array((rho[1],rho[1]+(rho[2]-rho[0])/6,rho[2]-(rho[3]-rho[1])/6,rho[2]));r.append(float(min(rho.min(),bc.min())))
 u,v=closest(xa,xb,t,t);pa,ta,_=evaluate(xa,u);pb,tb,_=evaluate(xb,v);tested+=1;res=disk_point(pa,ta,r[0],pb,tb,r[1],1e-6/sv.min())
 if res is None:
  point=(pa*r[1]+pb*r[0])/(r[0]+r[1]);na=ta/np.linalg.norm(ta);nb=tb/np.linalg.norm(tb);ea=float((point-pa)@na);eb=float((point-pb)@nb);ma=float(r[0]-np.linalg.norm(point-pa));mb=float(r[1]-np.linalg.norm(point-pb))
  if abs(ea)<1e-9 and abs(eb)<1e-9 and min(ma,mb)*sv.min()>2e-6:res=(point,ma,mb,ea,eb)
 if res is None:continue
 point,ma,mb,ea,eb=res;found.append({'sourceBundle':ci,'children':[ca,cb],'nativeSegment':seg,'parameters':[u,v],'commonInteriorPointLocal':point.tolist(),'commonInteriorPointWorldM':(A[:3,:3]@point+A[:3,3]).tolist(),'minimumRadialInteriorMarginsWorldM':[ma*float(sv.min()),mb*float(sv.min())],'nativePlaneResidualsLocal':[ea,eb],'nativeRadiusLowerBounds':r,'centerDistanceWorldM':float(np.linalg.norm(A[:3,:3]@(pa-pb))),'radiusLowerBoundCoversLinearAndCatmullRomInterpolants':True})
 if len(found)>=6:break
result={'status':'FAIL_COMMON_INTERIOR_FINITE_SHAFT_WITNESSES' if found else 'NO_WITNESS_IN_BOUNDED_CLOSEST_SEARCH_NOT_CONTACT_ACCEPTANCE','source':ref['output'],'sha256':ref['outputSha256'],'testedClosestParameterPairs':tested,'rankedSampleCandidates':len(candidates),'witnesses':found,'witnessesAreNotGlobalCount':True,'globalSignedMinimumM':None,'scope':'Actual evaluated saved native Catmull-Rom centre curves, circular local-radius cross sections under the saved affine object matrix. Common interior cross-section points, with numerical plane residuals and radial margins, falsify disjoint shaft volumes. No end-taper, whole-hair, body, dynamic or runtime pass.','sameParameterSearchWasReplacedAsOverrestrictive':True,'seconds':time.time()-tick};(E/'b-actual-micro-contact.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('R79_CLOSEST_MICRO_CONTACT',result['status'],tested,len(found),time.time()-tick,flush=True)
