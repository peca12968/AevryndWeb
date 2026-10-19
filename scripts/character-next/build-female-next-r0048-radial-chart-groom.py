"""Different representation: actual same-head exterior radial guide chart.

No root-frame copying, intrinsic triangle unfolding, centreline pushing or
contact-driven root changes. Positive radial exterior offsets do not certify
the interpolating POLY segments: actual finite capsules remain the gate.
"""
import bpy,importlib.util,numpy as np,time,math
from pathlib import Path
from mathutils import Vector
sp=importlib.util.spec_from_file_location('g48chart',Path(__file__).with_name('build-female-next-r0048-anatomical-groom.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
a.E=a.E/'b-radial-chart';a.E.mkdir(exist_ok=True);a.PILOT=a.S/'aevrynd-female-next-r0048-b-radial-guide-pilot.blend';a.OUT=a.S/'aevrynd-female-next-r0048-b-radial-wave-groom.blend'
a.METHOD='Actual same-current-head exterior radial chart: preserve authored source-guide angular displacements and nonnegative ray-defined exterior clearance; reconstruct each new-root path by exact ray queries on actual body. No rigid root-frame vector copying, unfolded surface transport, imported paths, fixed exit ring or clipping/pushing failed points. Independent finite-segment capsules gate expansion.'
a.INTERPOLATION='Three nearest same-part guide angular displacements and actual exterior radial offsets on this same head. Each source guide must round-trip without offset clamping. Ray exterior point is a coordinate chart, not an independent body proxy or collision certificate.'
ORIGINAL_DOMAIN=a.scalp_domain;TREE=None;QUERIES=0
def domain(V,T):
    global TREE
    # A whole-body exterior ray can hit a distant arm before a completely
    # exterior hair point. The coordinate chart is anatomical head/upper neck
    # only. ALL actual body triangles remain in a.main's independent gate.
    head=T[np.all(V[T,2]>=1.38,axis=1)];TREE=a.i.i.tree(V,head)
    a.save('chart-domain-correction.json',{'initialWholeBodyChartFailure':{'sourceGuidePointM':[-.1296936377669269,-.004038768347564259,1.339479649838997],'radialExteriorOffsetM':-.0896446490864928},'reason':'A fully exterior authored guide was behind the outer whole-body radial envelope because a distant shoulder/arm lies on the same ray. All29source guides separately passed actual whole-body finite capsules. Whole-body radial visibility is an invalid coordinate assumption, not a proven guide penetration.','coordinateDomain':'Actual existing head/upper-neck triangles with all three vertices worldZ>=1.38m; open patch, no invented cap/hull. Every query must hit; every original guide must have nonnegative exterior offset and roundtrip.','chartTriangles':len(head),'independentContactDomain':'All1,354,880actual evaluated body triangles, unchanged. No arm/shoulder contact exclusions, no root movement, no offset clamping or tolerance relaxation.'})
    return ORIGINAL_DOMAIN(V,T)
def exterior(az,el):
    global QUERIES
    d=np.array((math.cos(el)*math.sin(az),-math.cos(el)*math.cos(az),math.sin(el)));hit,normal,tid,dist=TREE.ray_cast(Vector(a.C+d*.70),Vector(-d),.75);QUERIES+=1
    if hit is None:raise ValueError(('Radial chart misses actual body',az,el))
    return float((np.array(hit)-a.C)@d),d
def followers(roots,normals,G,GN,which):
    tick=time.time();gaz=[];gel=[];gh=[];errors=[]
    for guide in G:
        az,el=a.angular(guide);az=np.unwrap(az);h=[]
        for j,(phi,theta)in enumerate(zip(az,el)):
            r,d=exterior(phi,theta);height=float(np.linalg.norm(guide[j]-a.C)-r)
            if height<0:raise ValueError(('Own source guide not in valid exterior radial chart',height,guide[j].tolist()))
            h.append(height);errors.append(float(np.linalg.norm(a.C+d*(r+height)-guide[j])))
        gaz.append(az-az[0]);gel.append(el-el[0]);gh.append(h)
    gaz=np.array(gaz);gel=np.array(gel);gh=np.array(gh);assert max(errors)<1e-6
    result=[];lineage=[];u=np.linspace(0,1,a.N);rng=np.random.default_rng(480248)
    for count,ci in enumerate(which):
        R0=roots[ci];D=np.linalg.norm(G[:,0]-R0,axis=1);same=(G[:,0,0]*R0[0]>=0)|(abs(G[:,0,0])<.009);D[~same]=np.inf;near=np.argsort(D)[:3];w=1/np.maximum(D[near],.001)**3;w/=w.sum();az,el=a.angular(R0[None]);phi=az[0]+w@gaz[near];theta=el[0]+w@gel[near];height=w@gh[near];P=[]
        # Shape variation is positive exterior volume, not a repair of failures.
        phase=float(rng.uniform(0,2*math.pi));height+=float(rng.uniform(.0001,.0004))*np.sin(math.pi*u)**2*(1+.5*np.sin(phase+7*math.pi*u))
        for ph,th,h in zip(phi,theta,height):
            r,d=exterior(float(ph),float(th));P.append(a.C+d*(r+h))
        P=np.array(P);P[0]=R0;result.append(P);lineage.append({'rootId':int(ci),'guides':near.tolist(),'weights':w.tolist(),'coordinateRepresentation':'Actual current-body exterior radial chart; no height clamping or contact-driven correction'})
        if count%1000==0:print('R48_RADIAL',count,len(which),QUERIES,time.time()-tick,flush=True)
        if time.time()-tick>720:raise TimeoutError('Bounded radial follower generation exceeded720seconds; no restart or unbounded retry')
    a.save('radial-chart-verification.json',{'sourceGuideRoundtripMaxErrorM':max(errors),'sourceGuideMinimumExteriorOffsetM':float(gh.min()),'sourceGuides':len(G),'bodyRayQueries':QUERIES,'generatedPaths':len(result),'coordinateChart':'Outermost actual head/upper-neck patch radial ray from0.70m exterior to head centre, same head only. Not assumed star-convex across other characters. Root points remain exact current body triangle/barycentric placements.','noOffsetClamping':True,'notAContactCertificate':True,'capsuleTestStillRequired':True,'seconds':time.time()-tick});return np.array(result),lineage
a.scalp_domain=domain;a.followers=followers
if __name__=='__main__':a.main()
