"""Continuous body separation for the static-head wind/control guide caches.

Linear centreline motion per physics interval is bounded around its temporal
midpoint segment by half the largest endpoint displacement. An exact segment
test with that inflated radius certifies the interval; uncertain spans split.
"""
import bpy,json,time,importlib.util,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
E=flow.R/'Evidence/character-female-next/r0015-guide-dynamics';S=flow.S;solid=flow.solid

def main():
    case=sys.argv[sys.argv.index('--case')+1] if '--case' in sys.argv else 'wind';sample=json.loads((E/f'c-{case}-actual-body-verification.json').read_text());assert sample['status']=='PASS_RECORDED_BODY_SAMPLES_ONLY';sim=json.loads((E/f'c-{case}-simulation.json').read_text());cache=Path(sim['output']);assert flow.route.sha(cache)==sim['outputSha256']==sample['cacheSha256'];motion=np.load(cache);P=motion['positions'].astype(np.float64);assert np.all(motion['headYawRadians']==0)
    driver=np.load(E/'driver-model.npz');report=json.loads((E/'driver-verification.json').read_text());bpy.ops.wm.open_mainfile(filepath=report['source']);solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');V,T,tree=solid.data(bpy.data.objects['AFN_R0008_Body']);V=np.array(V,dtype=np.float64);tri=V[np.array(T,dtype=np.int32)];A=driver['planeNormals'];offsets=np.max(V[driver['supportVertexIds']]@A.T,axis=0)+.000001;static={};failures=[];counts={'proxyCertifiedIntervals':0,'actualInflatedCapsuleCalls':0,'constantSegmentCacheHits':0,'adaptiveSplits':0,'maximumDepthUsed':0};minimum=float('inf');started=time.time();r=.00006;limit=8
    def certify(a,b,c,d,gi,j,depth=0):
        nonlocal minimum
        counts['maximumDepthUsed']=max(counts['maximumDepthUsed'],depth)
        constant=np.array_equal(a,c) and np.array_equal(b,d)
        key=(gi,j)
        if constant and key in static:counts['constantSegmentCacheHits']+=1;return static[key]
        mid_a=(a+c)*.5;mid_b=(b+d)*.5;inflate=.5*max(float(np.linalg.norm(c-a)),float(np.linalg.norm(d-b)));da=tree.find_nearest(Vector(mid_a))[3];db=tree.find_nearest(Vector(mid_b))[3];gap,method=flow.route.capsule.segment_test(mid_a,mid_b,da,db,r+inflate,tree,tri);counts['actualInflatedCapsuleCalls']+=1
        if gap>0:
            minimum=min(minimum,gap)
            if constant:static[key]=True
            return True
        if depth>=limit:return False
        counts['adaptiveSplits']+=1
        return certify(a,b,mid_a,mid_b,gi,j,depth+1) and certify(mid_a,mid_b,c,d,gi,j,depth+1)
    for fi in range(len(P)-1):
        p=P[fi];q=P[fi+1];va=(p.reshape(-1,3)@A.T-offsets).reshape(*p.shape[:2],-1);vb=(q.reshape(-1,3)@A.T-offsets).reshape(*q.shape[:2],-1);common=np.minimum(np.minimum(va[:,:-1],va[:,1:]),np.minimum(vb[:,:-1],vb[:,1:]));gap=np.max(common,axis=-1)-r-.000001;safe=(gap>0)&(np.minimum(p[:,:-1,2],q[:,:-1,2])>report['excludedBodyVertexMaximumZBoundOver25DegreeYawM']+r+.000001)&(np.minimum(p[:,1:,2],q[:,1:,2])>report['excludedBodyVertexMaximumZBoundOver25DegreeYawM']+r+.000001);counts['proxyCertifiedIntervals']+=int(safe.sum())
        for gi,j in np.argwhere(~safe):
            if not certify(p[gi,j],p[gi,j+1],q[gi,j],q[gi,j+1],int(gi),int(j)):failures.append({'interval':fi,'guide':int(gi),'segment':int(j),'startTimeS':float(motion['times'][fi]),'depthLimit':limit})
        if fi%120==0 or fi==len(P)-2:print('AFN15_SWEEP='+json.dumps({'case':case,'interval':fi,'failures':len(failures),**counts,'wallS':time.time()-started}),flush=True)
        if failures:break
    output={'case':case,'cacheSha256':sim['outputSha256'],'status':'PASS_CONTINUOUS_STATIC_BODY_GUIDE_SCOPE' if not failures and fi==len(P)-2 else 'FAIL_OR_UNRESOLVED','intervalsChecked':fi+1,'totalIntervals':len(P)-1,'guideSegmentIntervalPairs':int((fi+1)*P.shape[1]*(P.shape[2]-1)),'counts':counts,'failures':failures[:100],'minimumInflatedCapsuleClearanceLowerBoundM':minimum,'radiusM':r,'numericalAllowanceM':.000001,'bodySourceSha256':report['sourceSha256'],'method':'Shared support plane for the four endpoint positions, or midpoint complete segment capsule inflated by half the maximum endpoint motion; adaptive time subdivision to depth 8. Static actual body; world-linear guide interpolation.','scopeLimits':['Only the 48 guide centrelines/radius capsules and the static body in this exact cache.','No moving-head/root-corridor certificate, hair/hair self collision, optical/brow/lash checks or child interpolation.','This is not full groom or final character motion acceptance.'],'wallSeconds':time.time()-started}
    (E/f'c-{case}-continuous-body-verification.json').write_text(json.dumps(output,indent=2)+'\n');print('AFN15_SWEEP_DONE='+output['status'],flush=True)

if __name__=='__main__':main()
