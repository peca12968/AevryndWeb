"""Prove old collision state is unchanged; test only the newly authored brow geometry."""
import bpy,json,hashlib,array,math,importlib.util
import numpy as np
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0011-skin-brows';S=R/'engine/assets/characters/female-next/source'
SRC=S/'aevrynd-female-next-r0010-c-spaced-lashes-study.blend'; CAND=S/'aevrynd-female-next-r0011-b-ridge-skin-brows-study.blend'
spec=importlib.util.spec_from_file_location('prior_verifier',Path(__file__).with_name('verify-female-next-r0010-eye-rim.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def snapshot():
    result={}
    for o in bpy.data.objects:
        if o.type!='MESH' or o.name.startswith('AFN11_'):continue
        h=hashlib.sha256()
        for uv in o.data.uv_layers:
            a=array.array('f',[0.]*(len(uv.data)*2));uv.data.foreach_get('uv',a);h.update(a.tobytes())
        weights=[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]
        key_signature=[]
        if o.data.shape_keys:
            for k in o.data.shape_keys.key_blocks:
                a=array.array('f',[0.]*(len(k.data)*3));k.data.foreach_get('co',a);h.update(a.tobytes());key_signature.append((k.name,k.value,k.mute))
        result[o.name]={'geometry':base.geom(o),'UVAndShapeGeometry':h.hexdigest(),'weights':hashlib.sha256(json.dumps(weights,separators=(',',':')).encode()).hexdigest(),'shapeState':key_signature,
                        'matrix':list(v for row in o.matrix_world for v in row),'parent':o.parent.name if o.parent else None,'modifiers':[(m.type,getattr(m,'object',None).name if getattr(m,'object',None) else None,m.show_viewport,m.show_render) for m in o.modifiers]}
    rig=bpy.data.objects['AFN_R0005_Rig'];scene=bpy.context.scene
    return {'meshes':result,'rig':[(b.name,b.parent.name if b.parent else None,list(v for row in b.matrix_local for v in row)) for b in rig.data.bones],
            'lights':{o.name:{'matrix':list(v for row in o.matrix_world for v in row),'energy':o.data.energy,'size':o.data.size,'colour':list(o.data.color)} for o in bpy.data.objects if o.type=='LIGHT'},
            'colourManagement':{'transform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma}}

bpy.ops.wm.open_mainfile(filepath=str(SRC));old=snapshot(); inherited=json.loads((R/'Evidence/character-female-next/r0010-eye-rim/saved-collision-verification.json').read_text());old_cert=next(x for x in inherited['results'] if x['label']=='c-spaced-lashes');assert old_cert['status']=='PASS_TESTED_STATIC_POSES' and old_cert['fileSha256']==hashlib.sha256(SRC.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(CAND));now=snapshot();equality={k:old[k]==now[k] for k in old};assert all(equality.values()),equality
body=bpy.data.objects['AFN_R0008_Body'];rig=bpy.data.objects['AFN_R0005_Rig'];brows=sorted((o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN11_')),key=lambda o:o.name)
bindings=json.loads((E/'b-ridge-brow-bindings.json').read_text());structures={}
for o in brows:
    edge_counts={};parent=list(range(len(o.data.vertices)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for face in o.data.polygons:
        ids=list(face.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):key=tuple(sorted((a,b)));edge_counts[key]=edge_counts.get(key,0)+1;parent[find(a)]=find(b)
    sizes={}
    for i in range(len(parent)):key=find(i);sizes[key]=sizes.get(key,0)+1
    d={'hairs':len(sizes),'connectedComponentSizes':sorted(set(sizes.values())),'boundaryEdges':sum(v==1 for v in edge_counts.values()),'nonManifoldEdges':sum(v>2 for v in edge_counts.values()),'maximumWeightError':max(abs(sum(g.weight for g in v.groups)-1) for v in o.data.vertices),'nonFiniteVertices':sum(any(not math.isfinite(x) for x in v.co) for v in o.data.vertices)}
    assert d['boundaryEdges']==d['nonManifoldEdges']==d['nonFiniteVertices']==0 and d['maximumWeightError']<1e-6 and d['connectedComponentSizes']==[40]
    assert all(g.name in rig.data.bones for g in o.vertex_groups);structures[o.name]=d
poses={}
for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
    base.stage.set_pose(rig,pose); V,T,bodytree=base.data(body);tri=np.asarray([tuple(v) for v in V],dtype=np.float64)[np.asarray(T,dtype=np.int32)]
    targets={o.name:base.data(o) for o in bpy.data.objects if o.type=='MESH' and o.name in old['meshes'] and not o.hide_render};shots={o.name:base.data(o) for o in brows};rows={}
    for o in brows:
        P,PT,tree=shots[o.name];hits={name:len(tree.overlap(t[2])) for name,t in targets.items()}; self_pairs=[(a,b) for a,b in tree.overlap(tree) if a<b and set(PT[a]).isdisjoint(PT[b])]
        records=[x for x in bindings if x['object']==o.name];failures=[{'hair':x['hair'],'classification':c} for x in records if (c:=base.classify(bodytree,tri,P[x['firstVertex']]))!='outside']
        rows[o.name]={'targetTriangleIntersectionPairs':hits,'selfTriangleIntersectionPairs':len(self_pairs),'outsideConnectedHairAnchors':len(records)-len(failures),'containmentFailures':failures,'minimumSampledVertexBodyGapM':min(bodytree.find_nearest(p)[3] for p in P)}
    cross=len(shots[brows[0].name][2].overlap(shots[brows[1].name][2]));poses[pose]={'brows':rows,'betweenBrowTrianglePairs':cross}
    print('AFN_R0011_POSE='+json.dumps({'pose':pose,'targetCross':sum(sum(x['targetTriangleIntersectionPairs'].values()) for x in rows.values()),'selfCross':sum(x['selfTriangleIntersectionPairs'] for x in rows.values()),'containmentFailures':sum(len(x['containmentFailures']) for x in rows.values())}),flush=True)
clean=all(p['betweenBrowTrianglePairs']==0 and all(sum(x['targetTriangleIntersectionPairs'].values())==x['selfTriangleIntersectionPairs']==0 and not x['containmentFailures'] for x in p['brows'].values()) for p in poses.values())
report=json.loads((E/'female-next-r0011-b-ridge-skin-brows.report.json').read_text());assert hashlib.sha256(CAND.read_bytes()).hexdigest()==report['sha256']
images=[{'name':i.name,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images if i.source=='FILE'];assert all(x['packed'] for x in images)
result={'status':'PASS_TESTED_STATIC_POSES' if clean else 'FAIL_OR_UNRESOLVED','sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'candidateSha256':report['sha256'],'reopenedWithoutAddon':True,'originalStateEquality':equality,'structures':structures,'poses':poses,'packedImages':images,'externalLibraries':[l.filepath for l in bpy.data.libraries],
        'inheritedCollisionEvidence':{'path':str(R/'Evidence/character-female-next/r0010-eye-rim/saved-collision-verification.json'),'sha256':hashlib.sha256((R/'Evidence/character-female-next/r0010-eye-rim/saved-collision-verification.json').read_bytes()).hexdigest()},
        'distanceScope':'Brow vertices to body triangles only; not exact all-triangle minimum clearance.','limits':['Five static poses only; no blinking or swept movement.','Old body/eye/lash collision results inherited only after exact geometry/UV/weights/rig-state comparison.','No runtime materials or performance qualification.']}
assert not result['externalLibraries'];(E/'saved-collision-verification.json').write_text(json.dumps(result,indent=2)+'\n');print('AFN_R0011_VERIFIED='+result['status'])
