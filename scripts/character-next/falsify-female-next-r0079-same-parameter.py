"""Actual saved native circular cross-section intersection witness.
Affine image of a common interior point proves overlap; broad bounds alone do not.
Only implicated same-family pairs sampled, no global count/absence certificate.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0079-physical-filaments';sp=importlib.util.spec_from_file_location('disk79data',Path(__file__).with_name('qualify-female-next-r0075-dental-motion.py'));q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
def at(x,t):
 a,b,c,d=x;return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t**3),.5*((-a+c)+2*(2*a-5*b+4*c-d)*t+3*(-a+3*b-3*c+d)*t*t)
def disk_point(pa,na,ra,pb,nb,rb,margin):
 na=na/np.linalg.norm(na);nb=nb/np.linalg.norm(nb);delta=pb-pa;c=float(na@nb);den=1-c*c
 if den<1e-14:return None
 point=(nb-c*na)*(nb@delta)/den;direction=np.cross(na,nb);direction/=np.linalg.norm(direction);centers=[np.zeros(3),delta];radii=[ra,rb];intervals=[]
 for center,r in zip(centers,radii):
  rel=point-center;mid=-float(rel@direction);dist2=max(0.,float(rel@rel)-(rel@direction)**2)
  if dist2>=(r-margin)**2:return None
  half=np.sqrt((r-margin)**2-dist2);intervals.append((mid-half,mid+half))
 lo=max(v[0] for v in intervals);hi=min(v[1] for v in intervals)
 if lo>=hi:return None
 y=point+direction*(lo+hi)/2;x=pa+y;da=np.linalg.norm(x-pa);db=np.linalg.norm(x-pb);planeA=float((x-pa)@na);planeB=float((x-pb)@nb)
 if abs(planeA)>1e-8 or abs(planeB)>1e-8:return None
 return x,float(ra-da),float(rb-db),planeA,planeB
ref=q.read(E/'b-original-frame-build-summary.json');assert hashlib.sha256(Path(ref['output']).read_bytes()).hexdigest()==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=q.arr(d.position_data,'vector',len(d.position_data),3).astype('f8');rr=q.arr(d.attributes['radius'].data,'value',len(P)).astype('f8');A=np.array(o.matrix_world);sv=np.linalg.svd(A[:3,:3],compute_uv=False);z=np.load(E/'b-AFN68_MAIN_RENDER_CURVES-physical-lineage.npz');counts=z['counts'];starts=np.r_[0,np.cumsum(counts)[:-1]];curveType=d.attributes.get('curve_type');types=np.zeros(len(d.curves),'i4')
if curveType:curveType.data.foreach_get('value',types)
assert np.all(types==0),'This witness supports native Catmull-Rom only.'
found=[];tested=0;best=None
for n in np.unique(counts):
 ids=np.flatnonzero(counts==n)
 for ci in ids:
  base=int(starts[ci])*3;paths=[P[base+k*n:base+(k+1)*n] for k in range(3)];r=[rr[base+k*n:base+(k+1)*n] for k in range(3)]
  for seg in range(int(n)-4):
   idx=[max(0,seg-1),seg,seg+1,min(int(n)-1,seg+2)];rad=[]
   for k in range(3):
    radii=r[k][idx];bR=np.array((radii[1],radii[1]+(radii[2]-radii[0])/6,radii[2]-(radii[3]-radii[1])/6,radii[2]));rad.append(float(min(radii.min(),bR.min())))
   for t in (.25,.5,.75):
    values=[at(path[idx],t) for path in paths]
    for ca,cb in ((0,1),(0,2),(1,2)):
     pa,ta=values[ca];pb,tb=values[cb]
     if np.linalg.norm(pa-pb)>rad[ca]+rad[cb]:continue
     tested+=1;res=disk_point(pa,ta,rad[ca],pb,tb,rad[cb],1e-6/sv.min())
     if res is None:continue
     point,ma,mb,ea,eb=res;world=A[:3,:3]@point+A[:3,3];found.append({'sourceBundle':int(ci),'children':[ca,cb],'nativeSegment':seg,'nativeParameter':t,'commonInteriorPointLocal':point.tolist(),'commonInteriorPointWorldM':world.tolist(),'minimumDiskRadialInteriorMarginsWorldM':[ma*float(sv.min()),mb*float(sv.min())],'nativePlaneResidualsLocal':[ea,eb],'nativeRadiusLowerBounds':[rad[ca],rad[cb]],'radiusBoundCoversLinearOrCatmullRomInterpolatedRadius':True})
     if len(found)>=6:break
    if len(found)>=6:break
   if len(found)>=6:break
  if len(found)>=6:break
 if len(found)>=6:break
result={'status':'FAIL_COMMON_INTERIOR_FINITE_SHAFT_WITNESSES' if found else 'NO_WITNESS_IN_BOUNDED_SEARCH_NOT_CONTACT_ACCEPTANCE','source':ref['output'],'sha256':ref['outputSha256'],'nativeCurveType':0,'implicitTypeAttributeUsesCatmullRomDefault':curveType is None,'representation':'Actual evaluated native Catmull-Rom centre curves; positive circular local radii under the saved affine matrix. Common interior cross-section point maps into both affine rendered tube volumes. Radius lower bound covers linear and Catmull-Rom interpolation. No end taper used.','testedCloseSamplePairs':tested,'witnesses':found,'witnessesAreNotGlobalCount':True,'globalSignedMinimumM':None,'naturalMotionOrBodyOrOtherFamilyContactsAccepted':False};(E/'b-actual-micro-contact.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('R79_ACTUAL_MICRO_CONTACT',result['status'],tested,len(found),flush=True)
