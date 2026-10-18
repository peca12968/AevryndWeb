"""Check only changed brow geometry; inherit exact unchanged head/hair cases."""
import bpy,json,math,importlib.util,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0018-layered-brows.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
R,S,E,SRC,DST=build.R,build.S,build.E,build.SRC,build.DST;solid=build.solid
def main():
    prefix=build.VARIANT+'-' if build.VARIANT!='a' else ''
    report=json.loads((E/(prefix+'saved-build-verification.json')).read_text());assert build.sha(DST)==report['outputSha256'] and build.sha(SRC)==report['sourceSha256']
    inheritedPath=R/'Evidence/character-female-next/r0017-volume-locks/c-exact-crown-transition/saved-surface-verification.json';inherited=json.loads(inheritedPath.read_text());assert inherited['candidateSha256']==build.sha(SRC) and inherited['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE' and len(inherited['poses'])==5
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=build.controls();bpy.ops.wm.open_mainfile(filepath=str(DST));assert build.controls()==before
    rig=bpy.data.objects['AFN_R0005_Rig'];brows=[bpy.data.objects['AFN11_'+side+'_BrowFibres'] for side in ('L','R')];bindings=json.loads(Path(report['browBindings']).read_text());assert build.sha(report['browBindings'])==report['browBindingsSha256']
    structures={}
    for o in brows:
        edges={};parents=list(range(len(o.data.vertices)))
        def find(i):
            while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
            return i
        for face in o.data.polygons:
            ids=list(face.vertices)
            for a,b in zip(ids,ids[1:]+ids[:1]):
                key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1;parents[find(a)]=find(b)
        sizes={}
        for i in range(len(parents)):r=find(i);sizes[r]=sizes.get(r,0)+1
        data={'fibres':len(sizes),'componentVertexCounts':sorted(set(sizes.values())),'boundaryEdges':sum(v==1 for v in edges.values()),'nonManifoldEdges':sum(v>2 for v in edges.values()),'nonFiniteVertices':sum(any(not math.isfinite(x) for x in v.co) for v in o.data.vertices),'maximumWeightSumError':max(abs(sum(g.weight for g in v.groups)-1) for v in o.data.vertices)}
        assert data['componentVertexCounts']==[40] and data['boundaryEdges']==data['nonManifoldEdges']==data['nonFiniteVertices']==0 and data['maximumWeightSumError']<1.e-6
        assert all(g.name in rig.data.bones for g in o.vertex_groups);structures[o.name]=data
    poses={}
    for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
        started=time.time();solid.stage.set_pose(rig,pose);V,T,bodyTree=solid.data(bpy.data.objects['AFN_R0008_Body']);tri=np.array(V,dtype=np.float64)[np.array(T,dtype=np.int32)]
        targets={o.name:solid.data(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN6_','AFN10_')) and not o.hide_render};shots={o.name:solid.data(o) for o in brows};rows={}
        for o in brows:
            P,PT,tree=shots[o.name];bodyPairs=len(tree.overlap(bodyTree));hits={name:len(tree.overlap(d[2])) for name,d in targets.items()};selfPairs=[(a,b) for a,b in tree.overlap(tree) if a<b and set(PT[a]).isdisjoint(PT[b])];records=[x for x in bindings if x['object']==o.name];failures=[];fallbacks=0
            for rec in records:
                p=P[rec['firstVertex']];state=solid.classify(bodyTree,tri,p)
                if state=='unresolved':
                    winding=solid.winding(tri,np.array(p,dtype=np.float64));state='outside' if abs(winding)<1.e-6 else 'inside' if abs(abs(winding)-1)<1.e-6 else 'unresolved';fallbacks+=1
                if state!='outside':failures.append({'hair':rec['hair'],'state':state})
            rows[o.name]={'bodyTriangleIntersectionPairs':bodyPairs,'targetTriangleIntersectionPairs':hits,'nonAdjacentSelfTriangleIntersectionPairs':len(selfPairs),'outsideConnectedStrandAnchors':len(records)-len(failures),'anchorFailures':failures,'float64WindingFallbacks':fallbacks,'minimumSampledVertexBodyGapM':min(bodyTree.find_nearest(p)[3] for p in P)}
        cross=len(shots[brows[0].name][2].overlap(shots[brows[1].name][2]));paths=[];radii=[]
        for o in bpy.data.objects:
            if o.type=='CURVES' and o.name.startswith('AFN14_'):
                p,r=build.base.v14.prior.native_paths(o);paths.extend(p);radii.extend(r)
        hair=build.base.v14.prior.secondary_surfaces(paths,radii,brows)
        poses[pose]={'brows':rows,'betweenBrowTrianglePairs':cross,'hairVsNewBrows':hair,'wallSeconds':time.time()-started}
        clean=all(v['betweenBrowTrianglePairs']==0 and all(x['bodyTriangleIntersectionPairs']==x['nonAdjacentSelfTriangleIntersectionPairs']==0 and sum(x['targetTriangleIntersectionPairs'].values())==0 and not x['anchorFailures'] for x in v['brows'].values()) and all(x['status']=='PASS_SURFACE_SEPARATION' for x in v['hairVsNewBrows'].values()) for v in poses.values())
        result={'candidate':str(DST),'candidateSha256':build.sha(DST),'sourceSha256':build.sha(SRC),'status':'PASS_CHANGED_BROWS_TESTED_STATIC_POSES' if clean else 'FAIL_OR_UNRESOLVED','originalHeadSkinEyesLashesHairRigLightMaterialStateExact':True,'structures':structures,'poses':poses,'inheritedEvidence':{'path':str(inheritedPath),'sha256':build.sha(inheritedPath),'scope':'Unchanged r0017 hair/body and hair/optics/lash surfaces in the same five poses. Old hair/brow checks replaced by this new proof.'},'distanceScope':'Minimum sampled brow-vertex to body-triangle distances only; not the global triangle-to-triangle minimum. BVH triangle intersections plus outside anchors test connected strand containment. Native float BVHs with epsilon=0; shared-vertex adjacency omitted only in within-brow self tests.','limits':['Five static samples only; no facial expression, brow morph, blink or continuous motion proof.','Brow nonadjacent self-triangle checks do not qualify full scalp-hair self collision.','No native runtime or performance acceptance.']}
        build.save(prefix+'saved-static-verification.json',result);print('R0018_STATIC '+pose+' '+result['status'],flush=True)
        if not clean:break
    assert not bpy.data.libraries and all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    print('R0018_STATIC_DONE',flush=True)
if __name__=='__main__':main()
