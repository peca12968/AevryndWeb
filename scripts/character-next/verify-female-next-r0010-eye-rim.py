"""Independent saved-file and static collision verification for new lash geometry."""
import bpy, json, hashlib, array, math, importlib.util, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0010-eye-rim'; S=R/'engine/assets/characters/female-next/source'
SRC=S/'aevrynd-female-next-r0009-a-slab-thickness-study.blend'
spec=importlib.util.spec_from_file_location('poses',Path(__file__).with_name('build-female-next-r0007-socket-clearance.py'))
stage=importlib.util.module_from_spec(spec); spec.loader.exec_module(stage)
DIRS=[Vector(v).normalized() for v in ((1,.371,.193),(-.317,1,.233),(.217,-.181,1),(-1,-.211,.317),(.193,.271,-1))]

def geom(o):
    h=hashlib.sha256(); m=o.data
    for field,container,kind,n in [('co',m.vertices,'f',3),('vertex_index',m.loops,'i',1),('loop_start',m.polygons,'i',1),('loop_total',m.polygons,'i',1)]:
        a=array.array(kind,[0]*(len(container)*n));container.foreach_get(field,a);h.update(a.tobytes())
    return h.hexdigest()

def state():
    rig=bpy.data.objects['AFN_R0005_Rig']; body=bpy.data.objects['AFN_R0008_Body']
    weights=[[(body.vertex_groups[g.group].name,g.weight) for g in v.groups if body.vertex_groups[g.group].name in rig.data.bones] for v in body.data.vertices]
    return {'geometry':{o.name:geom(o) for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('AFN10_')},
            'bodyDeformWeights':hashlib.sha256(json.dumps(weights,separators=(',',':')).encode()).hexdigest(),
            'rig':[(b.name,b.parent.name if b.parent else None,list(x for row in b.matrix_local for x in row)) for b in rig.data.bones],
            'sourceMeshTransforms':{o.name:list(x for row in o.matrix_world for x in row) for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('AFN10_')},
            'bodyModifiers':[(x.type,getattr(x,'object',None).name if getattr(x,'object',None) else None,x.show_viewport,x.show_render) for x in body.modifiers]}

def winding(tri,p):
    a=tri[:,0]-p; b=tri[:,1]-p; c=tri[:,2]-p; na=np.linalg.norm(a,axis=1); nb=np.linalg.norm(b,axis=1); nc=np.linalg.norm(c,axis=1)
    return float(np.sum(2*np.arctan2(np.einsum('ij,ij->i',a,np.cross(b,c)),na*nb*nc+np.einsum('ij,ij->i',a,b)*nc+np.einsum('ij,ij->i',b,c)*na+np.einsum('ij,ij->i',c,a)*nb))/(4*math.pi))

def classify(tree,tri,p):
    parities=[]
    for d in DIRS:
        q=p.copy(); count=0
        for _ in range(80):
            hit=tree.ray_cast(q,d,3.)[0]
            if hit is None:break
            q=hit+d*.000001; count+=1
        else:return 'unresolved'
        parities.append(count%2)
    if len(set(parities))==1:return 'inside' if parities[0] else 'outside'
    w=winding(tri,np.array(p,dtype=np.float64));return 'outside' if abs(w)<1e-6 else ('inside' if abs(abs(w)-1)<1e-6 else 'unresolved')

def data(o):
    return stage.evaluated(o)

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC)); source_state=state()
    prior=json.loads((R/'Evidence/character-female-next/r0009-optics/saved-optics-verification.json').read_text()); assert hashlib.sha256(SRC.read_bytes()).hexdigest()==prior['candidateSha256'] and prior['status']=='PASS'
    only_spaced='--only-spaced' in sys.argv
    reports=[json.loads((E/'female-next-r0010-c-spaced-lashes.report.json').read_text())] if only_spaced else [json.loads((E/'female-next-r0010-eye-rim.report.json').read_text()),json.loads((E/'female-next-r0010-b-organic-lashes.report.json').read_text())]
    previous=E/'saved-collision-verification.json'
    results=[x for x in json.loads(previous.read_text())['results'] if x['label']!='c-spaced-lashes'] if only_spaced and previous.exists() else []
    for report in reports:
        path=Path(report['output']); label='c-spaced-lashes' if 'c-spaced' in path.name else ('b-organic-lashes' if 'b-organic' in path.name else 'a-rim-lashes')
        binding_path=E/(label+'-lash-bindings.json')
        if not binding_path.exists():binding_path=E/'lash-bindings.json'
        bindings=json.loads(binding_path.read_text()); bpy.ops.wm.open_mainfile(filepath=str(path)); assert hashlib.sha256(path.read_bytes()).hexdigest()==report['sha256']
        candidate_state=state(); equality={k:candidate_state[k]==source_state[k] for k in source_state}; assert all(equality.values()),equality
        body=bpy.data.objects['AFN_R0008_Body']; rig=bpy.data.objects['AFN_R0005_Rig']; parts=[bpy.data.objects[n] for n in report['lashes']['objects']]
        groups={o.name:[x for x in bindings if x['object']==o.name] for o in parts}; neutral_structure={}
        for o in parts:
            o.data.calc_loop_triangles(); boundaries={}
            for face in o.data.polygons:
                ids=list(face.vertices)
                for a,b in zip(ids,ids[1:]+ids[:1]):key=tuple(sorted((a,b)));boundaries[key]=boundaries.get(key,0)+1
            parent=list(range(len(o.data.vertices)))
            def find(i):
                while parent[i]!=i:parent[i]=parent[parent[i]]; i=parent[i]
                return i
            for edge in o.data.edges:
                a,b=edge.vertices; parent[find(a)]=find(b)
            sizes={}
            for i in range(len(parent)):key=find(i);sizes[key]=sizes.get(key,0)+1
            assert len(sizes)==len(groups[o.name]) and all(v==66 for v in sizes.values())
            neutral_structure[o.name]={'connectedHairs':len(sizes),'boundaryEdges':sum(v==1 for v in boundaries.values()),'nonManifoldEdges':sum(v>2 for v in boundaries.values()),'maximumWeightSumError':max(abs(sum(g.weight for g in v.groups)-1.) for v in o.data.vertices),'nonFiniteVertices':sum(any(not math.isfinite(x) for x in v.co) for v in o.data.vertices)}
            assert all(x.name in rig.data.bones for x in o.vertex_groups)
        poses={}
        for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
            stage.set_pose(rig,pose); V,T,tree=data(body); tri=np.array([tuple(v) for v in V],dtype=np.float64)[np.array(T,dtype=np.int32)]
            optics={o.name:data(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')}; snapshots={o.name:data(o) for o in parts}; entries={}
            for o in parts:
                P,PT,ptree=snapshots[o.name]; cross=tree.overlap(ptree); minimum=min(tree.find_nearest(p)[3] for p in P)
                anchors=[(hair['hair'],hair['firstVertex']) for hair in groups[o.name]]
                contained=[{'hair':hair,'classification':classify(tree,tri,P[vi])} for hair,vi in anchors]; bad=[x for x in contained if x['classification']!='outside']
                eye_cross={name:len(ptree.overlap(v[2])) for name,v in optics.items()}
                selfpairs=[(a,b) for a,b in ptree.overlap(ptree) if a<b and set(PT[a]).isdisjoint(PT[b])]
                strand_cross=[(a,b) for a,b in selfpairs if PT[a][0]//66!=PT[b][0]//66]
                own_cross=[(a,b) for a,b in selfpairs if PT[a][0]//66==PT[b][0]//66]
                root_distances=[tree.find_nearest(sum((P[h['firstVertex']+i] for i in range(6)),Vector())/6.)[3] for h in groups[o.name]]
                entries[o.name]={'bodyTriangleCrossPairs':len(cross),'bodyVertexSampleMinimumGapM':minimum,'outsideConnectedHairAnchors':len(contained)-len(bad),'containmentFailures':bad,'eyeTriangleCrossPairs':eye_cross,'interStrandTrianglePairs':len(strand_cross),'intraStrandTrianglePairs':len(own_cross),'interStrandSamples':strand_cross[:10],'rootDistanceM':{'min':min(root_distances),'max':max(root_distances)}}
            pair_cross=[]
            for i,o in enumerate(parts):
                for p in parts[i+1:]:pair_cross.append({'pair':[o.name,p.name],'trianglePairs':len(snapshots[o.name][2].overlap(snapshots[p.name][2]))})
            poses[pose]={'parts':entries,'lashObjectPairs':pair_cross}
            print('AFN_R0010_POSE='+json.dumps({'variant':label,'pose':pose,'bodyCross':sum(e['bodyTriangleCrossPairs'] for e in entries.values()),'opticalCross':sum(sum(e['eyeTriangleCrossPairs'].values()) for e in entries.values()),'interStrand':sum(e['interStrandTrianglePairs'] for e in entries.values()),'containmentFailures':sum(len(e['containmentFailures']) for e in entries.values())}),flush=True)
        clean=all(e['bodyTriangleCrossPairs']==0 and not e['containmentFailures'] and sum(e['eyeTriangleCrossPairs'].values())==0 and e['interStrandTrianglePairs']==0 and e['intraStrandTrianglePairs']==0 for p in poses.values() for e in p['parts'].values()) and all(x['trianglePairs']==0 for p in poses.values() for x in p['lashObjectPairs']) and all(v['boundaryEdges']==v['nonManifoldEdges']==v['nonFiniteVertices']==0 and v['maximumWeightSumError']<1e-6 for v in neutral_structure.values())
        results.append({'label':label,'fileSha256':report['sha256'],'savedFileOpened':True,'originalStateEquality':equality,'structure':neutral_structure,'poses':poses,'status':'PASS_TESTED_STATIC_POSES' if clean else 'FAIL_OR_UNRESOLVED'})
        (E/'saved-collision-verification.json').write_text(json.dumps({'revision':'female-next-r0010','results':results,'method':'Inherited unchanged closed body/eye state; triangle intersections plus closed-body containment anchor per connected hair. Self and cross-object lash triangle tests.','limits':['Five sampled static poses only.','Vertex-to-triangle minimum gap is sampled, not an exact all-surface minimum.','No blink, swept animation or runtime benchmark.']},indent=2)+'\n')
    print('AFN_R0010_VERIFICATION_DONE')

if __name__=='__main__':main()
