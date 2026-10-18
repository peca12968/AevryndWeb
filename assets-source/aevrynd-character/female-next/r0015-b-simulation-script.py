"""Bounded reference experiments; do not expand children before guide gates."""
import json,math,time,hashlib,importlib.util,sys
import numpy as np
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0015-guide-dynamics';S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('xpbd',R/'engine/character/physics/groom_xpbd_reference.py');xpbd=importlib.util.module_from_spec(spec);spec.loader.exec_module(xpbd)

def root_frames(P):
    x=P[:,1]-P[:,0];x/=np.linalg.norm(x,axis=1,keepdims=True);n=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]);n/=np.linalg.norm(n,axis=1,keepdims=True);return np.stack((x,np.cross(n,x),n),axis=-1)

def simulate(case='calm',duration=3.,iterations=16,variant='a'):
    controls=json.loads((E/'solver-controls.json').read_text());assert controls['status']=='PASS_LIMITED_MATH_CONTROLS';report=json.loads((E/'driver-verification.json').read_text());driver=E/'driver-model.npz';assert hashlib.sha256(driver.read_bytes()).hexdigest()==report['driverDataSha256'];assert report['skinningMode']=='LBS'
    d=np.load(driver);G=d['guides'].astype(np.float64);V=d['bodyRestVertices'].astype(np.float64);W=d['headWeights'];axis=d['headAxisWorld'];pivot=d['headPivotWorld'];A=d['planeNormals'];sup=d['supportVertexIds'];ids=d['guideBodyVertices'];bc=d['guideBarycentrics'];F0=d['restGuideFrames'];solver=xpbd.GuideSolver(G,iterations=iterations)
    dt=1/240;steps=round(duration/dt);positions=[G.astype(np.float32)];angle_rows=[0.];metrics=[];previous_angle=None;offsets=None;previous_x=G.copy();previous_offsets=None;swept_bad=0;swept_total=0;minimum_z=float('inf');maximum_stretch=0.;minimum_plane_gap=float('inf');start=time.time();body_bound=float(np.linalg.norm(V[sup]-pivot,axis=1).max());body_cache={}
    for i in range(1,steps+1):
        t=i*dt;angle=xpbd.head_yaw(t) if case=='turn-stop' else 0.
        if angle!=previous_angle:
            key=float(angle)
            if key in body_cache:offsets,anchors=body_cache[key]
            else:
                v=xpbd.rotate_yaw(V[sup],axis,pivot,angle,W[sup]);offsets=np.max(v@A.T,axis=0)+report['supportSlackM'];pose=xpbd.rotate_yaw(V[ids.ravel()],axis,pivot,angle,W[ids.ravel()]).reshape(*ids.shape,3);F=root_frames(pose);root=np.einsum('ij,ijk->ik',bc,pose)+F[:,:,2]*.00020;rotation=F@np.swapaxes(F0,1,2);anchors=root[:,None,:]+np.einsum('gij,gnj->gni',rotation,G[:,:3]-G[:,:1]);body_cache[key]=(offsets.copy(),anchors.copy())
            previous_angle=angle
        wind=xpbd.wind(t) if case=='wind' else np.zeros(3);x=solver.step(dt,anchors,wind,A,offsets);stats=solver.statistics();maximum_stretch=max(maximum_stretch,stats['maximumRelativeStretch']);minimum_z=min(minimum_z,float(x[:,:,2].min()));gap=xpbd.segment_plane_gaps(x,A,offsets);minimum_plane_gap=min(minimum_plane_gap,float(gap.min()-.00006))
        if previous_offsets is not None:
            q0=(previous_x.reshape(-1,3)@A.T).reshape(*x.shape[:2],-1);q1=(x.reshape(-1,3)@A.T).reshape(*x.shape[:2],-1);bow=body_bound*(angle-angle_rows[-1])**2/8
            common=np.minimum(np.minimum(q0[:,3:-1],q0[:,4:]),np.minimum(q1[:,3:-1],q1[:,4:]))-np.maximum(previous_offsets,offsets)-bow;certificate=np.max(common,axis=-1)-.00006-.000001;swept_bad+=int(np.count_nonzero(certificate<=0));swept_total+=certificate.size
        positions.append(x.astype(np.float32));angle_rows.append(angle);previous_x=x.copy();previous_offsets=offsets.copy()
        if i%60==0 or i==steps:
            row={'step':i,'timeS':t,**stats,'minimumFreeProxyCapsuleGapM':float(gap.min()-.00006),'minimumZ':float(x[:,:,2].min())};metrics.append(row);print('AFN15_SIM='+json.dumps({'case':case,**row,'elapsedS':time.time()-start}),flush=True)
            partial={'case':case,'variant':variant,'dtS':dt,'stepsCompleted':i,'intendedSteps':steps,'metrics':metrics,'status':'RUNNING_REFERENCE_EXPERIMENT'};(E/f'{variant}-{case}-progress.json').write_text(json.dumps(partial,indent=2)+'\n')
        if not stats['finite'] or stats['maximumRelativeStretch']>.15:break
    cache=S/f'aevrynd-female-next-r0015-{variant}-{case}-guides.npz';np.savez_compressed(cache,positions=np.array(positions),times=np.arange(len(positions))*dt,headYawRadians=np.array(angle_rows),selectedGuideIds=d['selectedGuideIds'],rest=G.astype(np.float32))
    completed=len(positions)==steps+1;gate=completed and maximum_stretch<=.02 and minimum_plane_gap>0 and minimum_z>report['excludedBodyVertexMaximumZBoundOver25DegreeYawM']+.000061
    result={'case':case,'variant':variant,'driverSha256':report['driverDataSha256'],'solverSha256':hashlib.sha256((R/'engine/character/physics/groom_xpbd_reference.py').read_bytes()).hexdigest(),'output':str(cache),'outputSha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'dtS':dt,'durationS':duration,'completed':completed,'physicsSteps':len(positions)-1,'guides':len(G),'guidePoints':int(np.prod(G.shape[:2])),'iterations':iterations,'parameters':{'representativeBundleLinearDensityKgPerM':2.5e-4,'axialStiffnessN':5.,'twoEdgeBendComplianceMPerN':.10,'airDragPerS':2.,'gravityMPerS2':9.81,'windVelocityMPerS':1.1,'calibration':'Artist-set research parameters, not measured hair properties; no torsion or friction model.'},'maximumRelativeStretchAcrossAllSteps':maximum_stretch,'minimumFreeProxyCapsuleGapAcrossStepsM':minimum_plane_gap,'minimumGuideZM':minimum_z,'excludedBodyZBoundM':report['excludedBodyVertexMaximumZBoundOver25DegreeYawM'],'freeSegmentSweptCertificates':{'tested':swept_total,'unqualified':swept_bad,'scope':'Shared supporting-plane bound for linear world-space guide segments against analytically yawed body over each physics interval, excluding first three root-corridor segments. Unqualified does not by itself prove collision.'},'metrics':metrics,'preliminaryNumericalGate':'PASS' if gate else 'FAIL_OR_UNRESOLVED','actualBodyRootCorridorCheck':'PENDING','motionAcceptance':'NOT_QUALIFIED','wallSeconds':time.time()-start}
    (E/f'{variant}-{case}-simulation.json').write_text(json.dumps(result,indent=2)+'\n');print('AFN15_SIM_DONE='+json.dumps({k:v for k,v in result.items() if k not in ('metrics','parameters')}),flush=True)

if __name__=='__main__':
    case=sys.argv[sys.argv.index('--case')+1] if '--case' in sys.argv else 'calm';duration=float(sys.argv[sys.argv.index('--duration')+1]) if '--duration' in sys.argv else 3.;iterations=int(sys.argv[sys.argv.index('--iterations')+1]) if '--iterations' in sys.argv else 16;variant=sys.argv[sys.argv.index('--variant')+1] if '--variant' in sys.argv else 'a';simulate(case,duration,iterations,variant)
