"""Independent actual Blender body checks at every recorded physics sample.

The proxy handles provably separated capsules; all other complete segments use
the actual posed body BVH. This does not certify intervals between samples.
"""
import bpy,json,math,hashlib,importlib.util,sys,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
R,S=flow.R,flow.S;E=R/'Evidence/character-female-next/r0015-guide-dynamics';solid=flow.solid
spec=importlib.util.spec_from_file_location('xpbd',R/'engine/character/physics/groom_xpbd_reference.py');xpbd=importlib.util.module_from_spec(spec);spec.loader.exec_module(xpbd)

def main():
    variant=sys.argv[sys.argv.index('--variant')+1] if '--variant' in sys.argv else 'c-pilot';case=sys.argv[sys.argv.index('--case')+1] if '--case' in sys.argv else 'calm';result=json.loads((E/f'{variant}-{case}-simulation.json').read_text());path=Path(result['output']);assert flow.route.sha(path)==result['outputSha256'];d=np.load(path);driver=np.load(E/'driver-model.npz');report=json.loads((E/'driver-verification.json').read_text());assert flow.route.sha(E/'driver-model.npz')==result['driverSha256'];bpy.ops.wm.open_mainfile(filepath=report['source']);rig=bpy.data.objects['AFN_R0005_Rig'];body=bpy.data.objects['AFN_R0008_Body'];solid.stage.set_pose(rig,'neutral');A=driver['planeNormals'];sup=driver['supportVertexIds'];axis=driver['headAxisWorld'];pivot=driver['headPivotWorld'];restV=driver['bodyRestVertices'].astype(np.float64);W=driver['headWeights'];ids=driver['guideBodyVertices'];bc=driver['guideBarycentrics'];rows=[];bad=[];root_bad=[];last_angle=None;tested=0;proxy_count=0;actual_count=0;minimum=float('inf');root_error=0.;match_error=0.;started=time.time()
    for fi,(P,angle) in enumerate(zip(d['positions'],d['headYawRadians'])):
        P=P.astype(np.float64)
        if last_angle is None or float(angle)!=last_angle:
            rig.pose.bones['head'].rotation_euler[1]=float(angle);bpy.context.view_layer.update();me=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;me.calc_loop_triangles();a=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',a);V=a.reshape(-1,3).astype(np.float64);matrix=np.array(body.matrix_world);V=V@matrix[:3,:3].T+matrix[:3,3];ti=np.empty(len(me.loop_triangles)*3,dtype=np.int32);me.loop_triangles.foreach_get('vertices',ti);T=ti.reshape(-1,3);tree=BVHTree.FromPolygons(V,T,all_triangles=True);tri=V[T];offsets=np.max(V[sup]@A.T,axis=0)+.000001;match_error=max(match_error,float(np.linalg.norm(V-xpbd.rotate_yaw(restV,axis,pivot,float(angle),W),axis=1).max()));last_angle=float(angle)
        vals=(P.reshape(-1,3)@A.T-offsets).reshape(*P.shape[:2],-1);gap=np.max(np.minimum(vals[:,:-1],vals[:,1:]),axis=-1)-.00006-.000001;safe=(gap>0)&(np.minimum(P[:,:-1,2],P[:,1:,2])>report['excludedBodyVertexMaximumZBoundOver25DegreeYawM']+.000061);proxy_count+=int(safe.sum());tested+=safe.size;minimum=min(minimum,float(gap[safe].min()) if safe.any() else float('inf'))
        for gi,pathP in enumerate(P):
            state=solid.classify(tree,tri,Vector(pathP[0]))
            if state=='unresolved':
                winding=solid.winding(tri,pathP[0]);state='outside' if abs(winding)<1e-6 else 'inside' if abs(abs(winding)-1)<1e-6 else 'unresolved'
            if state!='outside':root_bad.append({'frame':fi,'guide':gi,'state':state})
            joints=np.flatnonzero(~safe[gi]);nearest={}
            for j in joints:
                for k in (j,j+1):
                    if k not in nearest:nearest[k]=tree.find_nearest(Vector(pathP[k]))[3]
                g,method=flow.route.capsule.segment_test(pathP[j],pathP[j+1],nearest[j],nearest[j+1],.00006,tree,tri);minimum=min(minimum,g);actual_count+=1
                if g<=0 and len(bad)<150:bad.append({'frame':fi,'timeS':float(d['times'][fi]),'guide':gi,'segment':int(j),'gapLowerBoundM':g,'method':method})
        points=V[ids];n=np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]);n/=np.linalg.norm(n,axis=1,keepdims=True);expected=np.einsum('ij,ijk->ik',bc,points)+n*.00020;root_error=max(root_error,float(np.linalg.norm(P[:,0]-expected,axis=1).max()))
        if fi%120==0 or fi==len(d['positions'])-1:
            row={'sample':fi,'timeS':float(d['times'][fi]),'bodyCapsulesTested':tested,'actualSurfaceFallbacks':actual_count,'badSamplesRecorded':len(bad),'rootFailures':len(root_bad),'maximumRootAnchorErrorM':root_error,'elapsedS':time.time()-started};rows.append(row);print('AFN15_BODY='+json.dumps(row),flush=True)
        if bad or root_bad:break
    completed=fi==len(d['positions'])-1;status='PASS_RECORDED_BODY_SAMPLES_ONLY' if completed and not bad and not root_bad and root_error<.000001 and match_error<.000002 else 'FAIL_OR_UNRESOLVED'
    output={'case':case,'variant':variant,'cacheSha256':result['outputSha256'],'sourceSha256':report['sourceSha256'],'status':status,'samplesChecked':fi+1,'totalSamples':len(d['positions']),'capsulesTested':tested,'proxyCertifiedCapsules':proxy_count,'actualBodySurfaceFallbacks':actual_count,'minimumConservativeGapLowerBoundM':minimum,'maximumRootAnchorErrorM':root_error,'maximumAnalyticVsBlenderVertexErrorM':match_error,'bodyFailureSamples':bad,'rootFailureSamples':root_bad[:150],'progress':rows,'scopeLimits':['Body only, at every recorded 1/240 s sample.','Root/near-proxy segments checked against actual posed Blender tessellation; other segments use a contained-body proxy and excluded-body Z bound.','Does not prove continuous root-corridor separation, self collision, optical parts or full child hair; no motion acceptance.']}
    (E/f'{variant}-{case}-actual-body-verification.json').write_text(json.dumps(output,indent=2)+'\n');print('AFN15_BODY_DONE='+status,flush=True)

if __name__=='__main__':main()
