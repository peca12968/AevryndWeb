"""Changed lip/body surfaces and affected existing components, five static poses."""
import bpy,json,time,importlib.util,sys
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0023-neutral-mouth.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
spec=importlib.util.spec_from_file_location('hair',Path(__file__).with_name('verify-female-next-r0014-scalp-flow.py'));hair=importlib.util.module_from_spec(spec);spec.loader.exec_module(hair)
PREFIX='b' if '--b' in sys.argv else 'a'
if PREFIX=='b':b.DST=b.S/'aevrynd-female-next-r0023-b-rest-lip-field-study.blend'
def main():
    report=json.loads((b.E/f'{PREFIX}-build-verification.json').read_text());assert b.sha(b.DST)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(b.DST));rig=bpy.data.objects['AFN_R0005_Rig'];body=bpy.data.objects['AFN_R0008_Body'];key=body.data.shape_keys.key_blocks[report['key']];weight=report['weight'];base=b.base.positions(body);target=np.empty_like(base);key.data.foreach_get('co',target.ravel());changed=np.any(base!=target,axis=1);parts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN6_','AFN10_','AFN11_'))];hairParts=[o for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN14_')];rows=[]
    sourceProof=b.R/'Evidence/character-female-next/r0018-brow-readability/c-saved-static-verification.json';originalProof=json.loads(sourceProof.read_text());assert originalProof['candidateSha256']==report['sourceSha256'] and originalProof['status']=='PASS_CHANGED_BROWS_TESTED_STATIC_POSES'
    for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
        started=time.time();b.solid.stage.set_pose(rig,pose);key.value=0.;bpy.context.view_layer.update();oldV,oldT,oldtree=b.solid.data(body);key.value=weight;bpy.context.view_layer.update();V,T,bodytree=b.solid.data(body);assert T==oldT;indices=np.array(T,np.int32);active=np.flatnonzero(changed[indices].any(axis=1));activeT=indices[active];local=BVHTree.FromPolygons(V,activeT.tolist(),all_triangles=True);overlap=local.overlap(bodytree);pairs=[(int(active[i]),j) for i,j in overlap if int(active[i])<j and set(T[int(active[i])]).isdisjoint(T[j])];activeSet=set(active.tolist());pairs.extend((j,int(active[i])) for i,j in overlap if j<int(active[i]) and j not in activeSet and set(T[int(active[i])]).isdisjoint(T[j]));pairs=sorted(set(pairs));componentRows={o.name:len(local.overlap(b.solid.data(o)[2])) for o in parts};activeVertices=np.unique(activeT);v=np.array(V,np.float64);ov=np.array(oldV,np.float64);low=np.minimum(v[activeVertices].min(0),ov[activeVertices].min(0));high=np.maximum(v[activeVertices].max(0),ov[activeVertices].max(0));hairRows={};hairFailures=[]
        for o in hairParts:
            paths,radii=hair.prior.native_paths(o);total=0;near=[];lower=float('inf')
            for ci,(p,r) in enumerate(zip(paths,radii)):
                A=p[:-1];B=p[1:];radius=np.maximum(r[:-1],r[1:]);sep=np.maximum(np.max(np.minimum(A,B)-high,axis=1),np.max(low-np.maximum(A,B),axis=1))-radius-.000001;total+=len(A);lower=min(lower,float(sep.min()));ids=np.flatnonzero(sep<=0)
                for j in ids:near.append((ci,int(j),p[j],p[j+1],float(radius[j])))
            failures=[]
            for ci,j,A,B,r in near:
                da=local.find_nearest(Vector(A))[3];db=local.find_nearest(Vector(B))[3];gap,method=hair.flow.route.capsule.segment_test(A,B,da,db,r,local,v[activeT])
                if gap<=0:failures.append({'curve':ci,'segment':j,'gapLowerBoundM':gap,'method':method})
            hairRows[o.name]={'curves':len(paths),'segments':total,'unionOldNewLipBoxSeparatedSegments':total-len(near),'nearSegmentsCheckedExactly':len(near),'axisBoxSeparationLowerBoundM':lower if not near else None,'failures':len(failures),'failureSamples':failures[:20]};hairFailures.extend(failures)
        failures=len(pairs)+sum(componentRows.values())+len(hairFailures);rows.append({'pose':pose,'changedBodyTriangles':len(active),'changedBodyNonAdjacentSelfPairs':len(pairs),'selfPairSamples':pairs[:30],'lipVsExistingComponentTrianglePairs':componentRows,'hairVsChangedOldNewLipRegion':hairRows,'failureCount':failures,'wallSeconds':time.time()-started});b.save(f'{PREFIX}-saved-static-verification.json',{'asset':str(b.DST),'assetSha256':b.sha(b.DST),'sourceSha256':report['sourceSha256'],'inheritedSourceEvidence':{'path':str(sourceProof),'sha256':b.sha(sourceProof),'scope':'Unchanged source hair/component state only; changed lip region checked here.'},'status':'PASS_CHANGED_MOUTH_TESTED_STATIC_POSES' if all(r['failureCount']==0 for r in rows) else 'FAIL_OR_UNRESOLVED','poses':rows,'missingOralComponents':['Separate teeth','Separate tongue','Complete oral cavity lining'],'scope':'Changed body triangles vs full body and existing eye/brow/lash surfaces. Complete existing finite-radius hair segments bounded against the union old/new lip region, exact fallback when box separation cannot prove it. Five static poses only; no expression/continuous motion, complete oral anatomy or runtime acceptance.'});print('R0023_STATIC',pose,'FAILURES',failures,flush=True)
        if failures:break
    b.solid.stage.set_pose(rig,'neutral');key.value=weight;bpy.context.view_layer.update()
if __name__=='__main__':main()
