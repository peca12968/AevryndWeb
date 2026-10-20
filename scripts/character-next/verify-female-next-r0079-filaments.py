"""Saved B geometry control, source guide/root-frame lineage, finite shaft probes.
No global self/body/dynamic/engine certificate is inferred from samples.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,sys
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0079-physical-filaments'
ORIGINAL='--original-frame' in sys.argv
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
v=module('verify79native','verify-female-next-r0076-crowns.py');q=v.q;m=module('verify79render','build-female-next-r0074-oral-controls.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def cubic(x,t):
 x0=np.concatenate((x[:,:,:1],x[:,:,:-1]),axis=2);x3=np.concatenate((x[:,:,1:],x[:,:,-1:]),axis=2);a=x0[:,:,:-1];b=x[:,:,:-1];c=x[:,:,1:];d=x3[:,:,1:];value=.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);tangent=.5*((-a+c)+2*(2*a-5*b+4*c-d)*t+3*(-a+3*b-3*c+d)*t*t);return value,tangent

def main():
 tick=time.time();ref=q.read(E/('b-original-frame-build-summary.json' if ORIGINAL else 'b-source-material-control-summary.json'));b=q.read(E/'b-build-summary.json');assert sha(Path(b['source']))==b['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=b['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();names=list(q.read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());native={n:v.signature(bpy.data.objects[n]) for n in names};mats={n.name:m.m.k.f.v.v32.material_signature(n) for n in bpy.data.materials if n.use_nodes};lights=m.q.lights();oldHair=q.hair(bpy.data.objects['AFN68_MAIN_RENDER_CURVES']).copy();oldFly=q.hair(bpy.data.objects['AFN68_FLYAWAY_RENDER_CURVES']).copy();oldAttrs={}
 old=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'].data
 for at in old.attributes:
  if at.name.startswith('AFN69_'):oldAttrs[at.name]=q.arr(at.data,'vector' if at.data_type=='FLOAT_VECTOR' else 'value',len(at.data),3 if at.data_type=='FLOAT_VECTOR' else 1,'f4' if at.data_type=='FLOAT_VECTOR' else 'i4').copy()
 dental={n:q.arr(bpy.data.objects[n].data.vertices,'co',len(bpy.data.objects[n].data.vertices),3).copy() for n in ('AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID')};poses={}
 for deg in (0,-20,20):
  m.m.axis_pose(bpy.data.objects['AFN69_BODY_CONTROLS'],'Head',(0,0,1),deg);bpy.context.view_layer.update();poses[deg]=q.hair(bpy.data.objects['AFN68_MAIN_RENDER_CURVES']).copy()
 assert sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert {n:v.signature(bpy.data.objects[n]) for n in names}==native;assert {n:m.m.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert lights==m.q.lights();assert np.array_equal(oldFly,q.hair(bpy.data.objects['AFN68_FLYAWAY_RENDER_CURVES']))
 for n,p in dental.items():assert np.array_equal(q.arr(bpy.data.objects[n].data.vertices,'co',len(p),3),p)
 o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];d=o.data;z=np.load(E/'b-AFN68_MAIN_RENDER_CURVES-physical-lineage.npz');counts=z['counts'];starts=np.r_[0,np.cumsum(counts)[:-1]];newcounts=np.array([c.points_length for c in d.curves]);assert np.array_equal(newcounts,np.repeat(counts,3));assert np.max(np.abs(np.array(o.matrix_world)-(z['sourceMatrix'] if ORIGINAL else np.eye(4))))<1e-7
 for name,values in oldAttrs.items():
  at=d.attributes[name];actual=q.arr(at.data,'vector' if at.data_type=='FLOAT_VECTOR' else 'value',len(at.data),3 if at.data_type=='FLOAT_VECTOR' else 1,'f4' if at.data_type=='FLOAT_VECTOR' else 'i4');assert np.array_equal(actual,np.repeat(values,3,axis=0)),name
 radii=q.arr(d.attributes['radius'].data,'value',len(d.position_data));expected=np.full(len(radii),float(z['diameterM'])/2,'f4');newstarts=np.r_[0,np.cumsum(newcounts)[:-1]]
 for st,n in zip(newstarts,newcounts):expected[st+n-2]*=.8;expected[st+n-1]=5e-6
 if ORIGINAL:expected=np.load(E/'b-original-frame-radius-lineage.npz')['actualLocalRadius']
 assert np.array_equal(radii,expected);poseRows=[];rawNeutral=None
 for deg in (0,-20,20):
  m.m.axis_pose(bpy.data.objects['AFN69_BODY_CONTROLS'],'Head',(0,0,1),deg);bpy.context.view_layer.update();P=q.hair(o);mean=np.empty_like(oldHair)
  for n in np.unique(counts):
   ids=np.flatnonzero(counts==n);indices=starts[ids,None,None]*3+np.arange(3)[None,:,None]*n+np.arange(n)[None,None,:];sourceIds=starts[ids,None]+np.arange(n)[None,:];mean[sourceIds]=P[indices].mean(1)
  error=float(np.linalg.norm(mean-poses[deg],axis=1).max());print('R79_GUIDE_MEAN_POSE',ORIGINAL,deg,error,flush=True);save('b-original-frame-pose-progress.json' if ORIGINAL else 'b-unfixed-pose-progress.json',{'yaw':deg,'maximumActualGuideMeanErrorM':error,'toleranceM':2e-6,'passed':error<2e-6});assert error<2e-6;poseRows.append({'headYawDegrees':deg,'maximumFamilyMeanDifferenceFromOriginalActualGuideM':error})
  if deg==0:rawNeutral=P.copy()
 # Exact Catmull-Rom samples at shared parameters. A close sample is a
 # declared tube-model falsification, never a global count or no-contact pass.
 witness=[];tested=0;minimum=float('inf');rad=float(z['diameterM'])/2
 for n in np.unique(counts):
  ids=np.flatnonzero(counts==n);indices=starts[ids,None,None]*3+np.arange(3)[None,:,None]*n+np.arange(n)[None,None,:];P=rawNeutral[indices]
  for t in (.25,.5,.75):
   X,T=cubic(P,t);limit=max(0,int(n)-4)
   for a,c in ((0,1),(0,2),(1,2)):
    delta=X[:,a,:limit]-X[:,c,:limit];distance=np.linalg.norm(delta,axis=2);tested+=distance.size;minimum=min(minimum,float(distance.min()));avg=T[:,a,:limit]+T[:,c,:limit];avg/=np.linalg.norm(avg,axis=2)[:,:,None];axial=np.abs(np.einsum('ijk,ijk->ij',delta,avg));bad=np.argwhere((distance<2*rad-1e-6)&(axial<1e-6))
    for ci,seg in bad[:max(0,12-len(witness))]:witness.append({'sourceBundle':int(ids[ci]),'childA':a,'childB':c,'segment':int(seg),'parameter':t,'pointA':X[ci,a,seg].tolist(),'pointB':X[ci,c,seg].tolist(),'centerDistanceM':float(distance[ci,seg]),'twoShaftRadiiM':2*rad,'axialComponentAlongAverageTangentM':float(axial[ci,seg])})
 images=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file:
   path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.is_file();images.append({'relative':im.filepath,'sha256':sha(path)})
 assert len(images)==15 and not bpy.data.libraries
 result={'status':'PASS_SAVED_GEOMETRY_CONTROL_DATA_AND_GUIDE_MEAN_SCOPE_ONLY','source':ref['output'],'sha256':ref['outputSha256'],'allFiveNativeCagesKeysUVWeightsDriversExact':True,'allOriginalMaterialsIncludingActiveBrownHairExact':True,'lightsAndDentalVerticesAndActualNeutralFlyawayExact':True,'neutralAreaEquivalentWorldShaftDiameterM':float(z['diameterM']),'actualWorldSectionRepresentation':'original-affine ellipses; area calibrated at neutral native tangents' if ORIGINAL else 'circular identity-object representation','terminalRadiusM':5e-6,'actualCurves':len(newcounts),'actualPoints':len(radii),'parentRootFrameIDsAndBarycentricsRepeatedExactly':True,'actualGuideMeanPoses':poseRows,'sameParameterMicroTubeProbe':{'status':('UNRESOLVED_EQUIVALENT_CIRCLE_SAMPLES_NOT_ACTUAL_ELLIPSE_PENETRATION' if witness else 'NO_EQUIVALENT_CIRCLE_SAMPLE_WITNESS_NOT_CONTACT_CERTIFICATE') if ORIGINAL else ('FAIL_DECLARED_FINITE_TUBE_SAMPLES' if witness else 'NO_STRONG_SAMPLED_OVERLAP_NOT_SELF_CONTACT_CERTIFICATE'),'testedShaftPairParameters':tested,'minimumSampledCenterDistanceM':minimum,'shaftDiameterM':2*rad,'numericalWitnessThresholdM':1e-6,'witnesses':witness,'samplesAreNotGlobalMinimumOrGlobalCount':True,'endTaperExcludedFromConstantRadiusWitnessTest':True,'actualEllipseSurfaceAndAllCrossParameterPairsNotCertified':ORIGINAL,'pointSamplesNotClaimedAsActualEllipticalSurfaceCrossing':ORIGINAL},'naturalHairDynamicsFollicleSelfBodyContinuousAndRuntimeAccepted':False,'originalKnownMovedHairBodyRiskUnresolved':True,'externalTextures':images,'seconds':time.time()-tick};save('b-original-frame-readback.json' if ORIGINAL else 'b-geometry-control-readback.json',result);print('R79_GEOMETRY_CONTROL_READBACK',poseRows,result['sameParameterMicroTubeProbe']['status'],minimum,time.time()-tick,flush=True)
if __name__=='__main__':main()
