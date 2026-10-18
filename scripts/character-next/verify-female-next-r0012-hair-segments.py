"""Conservative capsule/body separation of full POLY strands, not just CV samples."""
import bpy,numpy as np,json,math,hashlib,importlib.util,sys,time
from pathlib import Path
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair';S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('solid',Path(__file__).with_name('verify-female-next-r0010-eye-rim.py'));solid=importlib.util.module_from_spec(spec);spec.loader.exec_module(solid)

def segment_edges(A,B,C,D):
    """Exact minimum over finite segment pairs: interior solution plus four boundaries."""
    u=B-A;v=D-C;w=A-C;a=float(u@u);c=np.einsum('ij,ij->i',v,v);b=v@u;d=w@u;e=np.einsum('ij,ij->i',v,w);den=a*c-b*b
    safe=np.where(abs(den)>1e-24,den,1.);s=(b*e-c*d)/safe;t=(a*e-b*d)/safe
    valid=(abs(den)>1e-24)&(s>=0)&(s<=1)&(t>=0)&(t<=1)
    distances=np.where(valid,np.linalg.norm(A+s[:,None]*u-(C+t[:,None]*v),axis=1),np.inf)
    for P in (A,B):
        x=np.clip(np.einsum('ij,ij->i',P-C,v)/np.maximum(c,1e-30),0,1);distances=np.minimum(distances,np.linalg.norm(P-C-x[:,None]*v,axis=1))
    for P in (C,D):
        x=np.clip((P-A)@u/max(a,1e-30),0,1);distances=np.minimum(distances,np.linalg.norm(P-A-x[:,None]*u,axis=1))
    return float(distances.min())

def segment_test(A,B,da,db,r,tree,tri):
    """A positive lower bound proves the swept radius stays outside the body surface."""
    u=B-A;L=float(np.linalg.norm(u));tolerance=.000001;search_margin=.000010
    if L<1e-12:return da-r-tolerance,'point'
    lower=(da+db-L)*.5-r-tolerance
    if lower>0:return lower,'lipschitz'
    hit=tree.ray_cast(Vector(A),Vector(u/L),L)[0]
    if hit is not None:return -r,'centreline_cross'
    found=tree.find_nearest_range(Vector((A+B)*.5),L*.5+r+search_margin)
    if not found:return search_margin-tolerance,'range_empty'
    ids=np.array(sorted({f[2] for f in found}),dtype=np.int32);faces=tri[ids];C=faces.reshape(-1,3);D=faces[:,[1,2,0]].reshape(-1,3)
    distance=min(da,db,segment_edges(A,B,C,D));bound=min(distance,r+search_margin)-r-tolerance
    return bound,'edge_distance'

def math_controls():
    z=np.array([0.,0.,0.]);x=np.array([1.,0.,0.])
    assert abs(segment_edges(z,x,np.array([[.5,-1,0]]),np.array([[.5,1,0]])))<1e-12
    assert abs(segment_edges(z,x,np.array([[0,1,0]]),np.array([[1,1,0]]))-1)<1e-12
    assert abs(segment_edges(z,x,np.array([[2,0,0]]),np.array([[3,0,0]]))-1)<1e-12
    assert abs(segment_edges(z,x,np.array([[.5,-1,2]]),np.array([[.5,1,2]]))-2)<1e-12

def main():
    math_controls();label='c-corrected-hair' if '--corrected' in sys.argv else 'b-volume-hair';path=S/('aevrynd-female-next-r0012-'+label+'-study.blend');bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['AFN_R0005_Rig'];body=bpy.data.objects['AFN_R0008_Body'];parts=sorted((o for o in bpy.data.objects if o.type=='CURVE' and o.name.startswith('AFN12_') and not o.hide_render),key=lambda o:o.name)
    poses=('neutral',) if '--neutral-only' in sys.argv else ('neutral','gaze-left','gaze-right','turn-left','turn-right');results={}
    for pose in poses:
        solid.stage.set_pose(rig,pose);V,T,tree=solid.data(body);tri=np.array([tuple(v) for v in V],dtype=np.float64)[np.array(T,dtype=np.int32)];rows={}
        for o in parts:
            failures=[];total_bad=0;segments=0;minimum=float('inf');min_cv=float('inf');methods={};inside=0;start=time.time()
            for ci,c in enumerate(o.data.splines):
                P=np.array([tuple(o.matrix_world@Vector(p.co[:3])) for p in c.points],dtype=np.float64);radii=np.array([p.radius*o.data.bevel_depth for p in c.points]);ds=[tree.find_nearest(Vector(p))[3] for p in P];min_cv=min(min_cv,min(ds-radii))
                state=solid.classify(tree,tri,Vector(P[0]));inside+=state!='outside'
                for j in range(len(P)-1):
                    gap,method=segment_test(P[j],P[j+1],ds[j],ds[j+1],float(max(radii[j],radii[j+1])),tree,tri);methods[method]=methods.get(method,0)+1;segments+=1;minimum=min(minimum,gap)
                    if gap<=0:
                        total_bad+=1
                        if len(failures)<120:failures.append({'curve':ci,'segment':j,'clearanceLowerBoundM':gap,'method':method,'a':P[j].tolist(),'b':P[j+1].tolist()})
            rows[o.name]={'curves':len(o.data.splines),'segments':segments,'unqualifiedSegments':total_bad,'rootContainmentFailures':inside,'minimumCertifiedCapsuleClearanceLowerBoundM':minimum,'minimumSampledCVSurfaceGapM':min_cv,'methods':methods,'failureSamples':failures,'verificationWallSeconds':time.time()-start}
            print('AFN_R0012_SEGMENT='+json.dumps({'pose':pose,'object':o.name,'curves':len(o.data.splines),'badSegments':total_bad,'insideRoots':inside,'wallSeconds':time.time()-start}),flush=True)
        results[pose]=rows
        status='PASS_TESTED_CAPSULE_BODY_POSES' if all(x['unqualifiedSegments']==x['rootContainmentFailures']==0 for p in results.values() for x in p.values()) else 'FAIL_OR_UNRESOLVED'
        (E/(label+'-segment-verification.json')).write_text(json.dumps({'status':status,'candidate':str(path),'candidateSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'poses':results,'method':'Capsule per actual saved POLY segment with max endpoint radius; Lipschitz bound, exact centreline ray test and finite segment/body triangle-edge distances. Closed-body root parity anchors.','numericalAllowanceM':.000001,'broadphaseExtraMarginM':.000010,'mathControlCasesPassed':True,'scopeLimits':['Body only; optical components/brows/lashes and hair/hair separation are not certified here.','Static poses, not swept dynamics.','Lower bounds are conservative and are not exact global minimum gaps.']},indent=2)+'\n')
    print('AFN_R0012_SEGMENT_DONE')

if __name__=='__main__':main()
