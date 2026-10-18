"""Certify static eye/body separation using closed-solid topology and containment.

Nearest-face normal signs remain raw diagnostics. A closed non-self-intersecting
body and a connected optical surface with no triangle crossings have constant
inside/outside classification. Anchors and every raw-negative point are checked
by five ray parities; disagreements use a double-precision solid-angle winding
sum. See https://igl.ethz.ch/projects/winding-number/ for the winding principle.
No libigl code or dependency is used.
"""
import bpy,json,math,hashlib,importlib.util
import numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0008-evaluated-sockets'
spec=importlib.util.spec_from_file_location('afn_solid_pose',Path(__file__).with_name('build-female-next-r0007-socket-clearance.py'));tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)
DIRECTIONS=[Vector(v).normalized() for v in ((1.,.371,.193),(-.317,1.,.233),(.217,-.181,1.),(-1.,-.211,.317),(.193,.271,-1.))]
POSES=('neutral','gaze-left','gaze-right','turn-left','turn-right')

def components(mesh):
    parent=list(range(len(mesh.vertices)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for edge in mesh.edges:
        a,b=edge.vertices;ra,rb=find(a),find(b)
        if ra!=rb:parent[ra]=rb
    return len({find(i) for i in range(len(parent))})

def ray_count(tree,p,d):
    p=p.copy();n=0
    for step in range(80):
        hit=tree.ray_cast(p,d,3.)
        if hit[0] is None:return n
        n+=1;p=hit[0]+d*.000001
    return None

def winding(triangles,p):
    q=np.array(p,dtype=np.float64);a=triangles[:,0]-q;b=triangles[:,1]-q;c=triangles[:,2]-q
    na=np.linalg.norm(a,axis=1);nb=np.linalg.norm(b,axis=1);nc=np.linalg.norm(c,axis=1)
    numerator=np.einsum('ij,ij->i',a,np.cross(b,c));denominator=na*nb*nc+np.einsum('ij,ij->i',a,b)*nc+np.einsum('ij,ij->i',b,c)*na+np.einsum('ij,ij->i',c,a)*nb
    return float(np.sum(2*np.arctan2(numerator,denominator),dtype=np.float64)/(4*math.pi))

report=json.loads((E/'female-next-r0008-evaluated-sockets.report.json').read_text());results=[]
for variant in report['variants']:
    path=Path(variant['output']);bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['AFN_R0008_Body'];rig=bpy.data.objects['AFN_R0005_Rig'];parts=sorted((o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')),key=lambda o:o.name)
    counts=Counter();orientation=Counter()
    for poly in body.data.polygons:
        ids=list(poly.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):key=tuple(sorted((a,b)));counts[key]+=1;orientation[key]+=1 if a<b else -1
    topology={'bodyComponents':components(body.data),'bodyBoundaryEdges':sum(n==1 for n in counts.values()),'bodyNonManifoldEdges':sum(n>2 for n in counts.values()),'inconsistentEdgeOrientations':sum(n!=0 for n in orientation.values())}
    part_connectivity={o.name:components(o.data) for o in parts};poses={}
    for pose in POSES:
        tools.set_pose(rig,pose);V,T,tree=tools.evaluated(body);selfpairs=[(a,b) for a,b in tree.overlap(tree) if a<b and set(T[a]).isdisjoint(T[b])];triangle_array=np.asarray([list(v) for v in V],dtype=np.float64)[np.asarray(T,dtype=np.int32)]
        controls={'insideWinding':winding(triangle_array,(0.,0.,1.0)),'outsideWinding':winding(triangle_array,(2.,2.,2.))}
        control_ok=abs(abs(controls['insideWinding'])-1)<1e-6 and abs(controls['outsideWinding'])<1e-6
        pose_results={};dg=bpy.context.evaluated_depsgraph_get()
        for part in parts:
            pe=part.evaluated_get(dg);m=pe.to_mesh();P=[pe.matrix_world@v.co for v in m.vertices];m.calc_loop_triangles();PT=[tuple(t.vertices) for t in m.loop_triangles];ptree=BVHTree.FromPolygons(P,PT,all_triangles=True);cross=tree.overlap(ptree);negative=[];minimum=float('inf')
            for i,p in enumerate(P):
                hit=tree.find_nearest(p);minimum=min(minimum,hit[3])
                if (p-hit[0]).dot(hit[1].normalized())<0:negative.append(i)
            anchors={0,len(P)//3,2*len(P)//3,len(P)-1};queries=sorted(set(negative)|anchors);classifications=Counter();fallbacks=[];anchor_results=[]
            for i in queries:
                p=P[i];rays=[ray_count(tree,p,d) for d in DIRECTIONS];parities=[n%2 if n is not None else None for n in rays]
                if all(n==0 for n in parities):kind='outside'
                elif all(n==1 for n in parities):kind='inside'
                else:
                    w=winding(triangle_array,p);kind='outside' if abs(w)<1e-6 else ('inside' if abs(abs(w)-1)<1e-6 else 'unresolved');fallbacks.append({'vertex':i,'rayCounts':rays,'winding':w,'classification':kind})
                classifications[kind]+=1
                if i in anchors:anchor_results.append({'vertex':i,'classification':kind,'rayCounts':rays})
            outside=(classifications['inside']==classifications['unresolved']==0 and len(cross)==0 and part_connectivity[part.name]==1 and control_ok and len(selfpairs)==0 and topology['bodyComponents']==1 and topology['bodyBoundaryEdges']==topology['bodyNonManifoldEdges']==topology['inconsistentEdgeOrientations']==0 and minimum>0)
            pose_results[part.name]={'vertices':len(P),'componentCount':part_connectivity[part.name],'bodyTriangleCrossPairs':len(cross),'rawNearestNormalNegativeVertices':len(negative),'containmentQueries':len(queries),'queryClassifications':dict(classifications),'windingFallbacks':fallbacks,'anchors':anchor_results,'minimumUnsignedDistanceM':minimum,'certifiedInsideVertices':0 if outside else None,'status':'CLOSED_SOLID_SEPARATION_PASS' if outside else 'UNQUALIFIED'};pe.to_mesh_clear()
        poses[pose]={'bodySelfPairs':len(selfpairs),'windingControls':controls,'controlPassed':control_ok,'parts':pose_results}
        print('AFN_R0008_SOLID_POSE='+json.dumps({'variant':variant['label'],'pose':pose,'allPartsPass':all(p['status']=='CLOSED_SOLID_SEPARATION_PASS' for p in pose_results.values()),'rawNegative':sum(p['rawNearestNormalNegativeVertices'] for p in pose_results.values()),'windingFallbacks':sum(len(p['windingFallbacks']) for p in pose_results.values())}),flush=True)
    tools.set_pose(rig,'neutral')
    status='PASS_TESTED_STATIC_POSES' if all(p['status']=='CLOSED_SOLID_SEPARATION_PASS' for a in poses.values() for p in a['parts'].values()) else 'FAIL_OR_UNRESOLVED'
    results.append({'label':variant['label'],'fileSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'topology':topology,'poses':poses,'status':status})
    (E/'closed-solid-verification.json').write_text(json.dumps({'revision':'female-next-r0008','method':'Closed oriented non-self-intersecting body + connected optical components + no triangle crossings + outside anchor/negative-point containment','distanceScope':'Eye vertices to body triangles. Reported minimumUnsignedDistanceM is a sampled vertex clearance, not an exact all-triangle minimum gap or a swept-distance bound.','rayDirections':[list(d) for d in DIRECTIONS],'rayStepM':.000001,'windingPrecision':'float64 solid-angle sum','windingThreshold':1e-6,'results':results,'limits':['Static sampled poses only; no continuous swept collision.','Body/eye component separation only; no eye/eye optical interface or blink qualification.','No runtime performance or whole-character quality acceptance.']},indent=2)+'\n')
