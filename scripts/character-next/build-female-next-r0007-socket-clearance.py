"""Expand only localized, occluded native socket surfaces around fixed r0006 eyes."""
import bpy, json, math, hashlib, importlib.util
from pathlib import Path
from collections import defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0007-socket-clearance';E.mkdir(parents=True,exist_ok=True)
SRC=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0006-b-balanced-study.blend'
spec=importlib.util.spec_from_file_location('afn_eye_tools',Path(__file__).with_name('build-female-next-r0006-native-eyes.py'));eyes=importlib.util.module_from_spec(spec);spec.loader.exec_module(eyes);eyes.E=E
data=json.loads((R/'Evidence/character-female-next/r0006-native-eyes/saved-eye-verification.json').read_text());local=next(x for x in data['results'] if x['label']=='b-balanced')['neutralContactLocalization']
VARIANTS=(('a-tight',.0003),('b-balanced',.0007),('c-reserved',.0012))

def evaluated(body):
    dg=bpy.context.evaluated_depsgraph_get();dg.update();ev=body.evaluated_get(dg);m=ev.to_mesh();V=[ev.matrix_world@v.co for v in m.vertices];m.calc_loop_triangles();T=[tuple(t.vertices) for t in m.loop_triangles];tree=BVHTree.FromPolygons(V,T,all_triangles=True);ev.to_mesh_clear();return V,T,tree

def set_pose(rig,pose):
    eyes.set_pose(rig,'neutral')
    if pose in ('gaze-left','gaze-right'):
        for side in ('L','R'):rig.pose.bones['eye.'+side].rotation_euler[2]=math.radians(10 if pose=='gaze-left' else -10)
    if pose in ('turn-left','turn-right'):rig.pose.bones['head'].rotation_euler[1]=math.radians(20 if pose=='turn-left' else -20)
    bpy.context.view_layer.update()

def eye_front(point,centre,radius):
    r2=(point.x-centre.x)**2+(point.z-centre.z)**2
    return centre.y-math.sqrt(radius*radius-r2) if r2<radius*radius else None

def repair(body,fits,margin):
    mesh=body.data;original=[v.co.copy() for v in mesh.vertices];V,T,tree=evaluated(body);free=set();locked=set();centres={s:Vector(fits[s]['centre']) for s in ('L','R')}
    # Spherical envelope includes the corneal apex through the bounded gaze range.
    envelope={s:max((Vector(v.co)-centres[s]).length for obj in bpy.data.objects if obj.name.startswith('AFN6_'+s+'_') for v in obj.data.vertices) for s in ('L','R')}
    adjacency=defaultdict(set)
    for edge in mesh.edges:
        a,b=edge.vertices;adjacency[a].add(b);adjacency[b].add(a)
    selections={}
    for side in ('L','R'):
        faces=set(i for name,x in local.items() if name.startswith('AFN6_'+side+'_') for i in x['nearestNativeControlFaces'])
        candidate={i for fi in faces for i in mesh.polygons[fi].vertices}
        for _ in range(2):candidate |= {j for i in list(candidate) for j in adjacency[i]}
        selected=[];protected=[]
        for i in sorted(candidate):
            p=body.matrix_world@original[i]
            if (p-centres[side]).length>.032:continue
            h=tree.find_nearest(p)[0];front=tree.ray_cast(Vector((h.x,-.4,h.z)),Vector((0.,1.,0.)),.5)[0]
            eyeY=eye_front(h,centres[side],envelope[side])
            body_front=front is not None and abs(front.y-h.y)<.00015
            covered=eyeY is not None and eyeY<h.y-.00015
            if body_front and not covered:locked.add(i);protected.append(i)
            else:free.add(i);selected.append(i)
        selections[side]={'candidateVertices':len(candidate),'freeVertices':selected,'lockedVisibleVertices':protected,'envelopeRadiusM':envelope[side]}
    free-=locked
    movements=[]
    for i in sorted(free):
        p=body.matrix_world@original[i];side=min(centres,key=lambda s:(p-centres[s]).length);d=p-centres[side];target=envelope[side]+margin
        if d.length>=target:continue
        q=centres[side]+d.normalized()*target;delta=q-p;mesh.vertices[i].co=original[i]+body.matrix_world.inverted().to_3x3()@delta;movements.append({'vertex':i,'deltaM':list(delta),'lengthM':delta.length})
    mesh.update();after,_,_=evaluated(body)
    visible_limit=[]
    for i,p in enumerate(V):
        side=min(centres,key=lambda s:(p-centres[s]).length)
        if (p-centres[side]).length>.030:continue
        front=tree.ray_cast(Vector((p.x,-.4,p.z)),Vector((0.,1.,0.)),.5)[0]
        ey=eye_front(p,centres[side],envelope[side])
        if front is not None and abs(front.y-p.y)<.00005 and (ey is None or p.y<ey-.0001):visible_limit.append((after[i]-p).length)
    return {'marginM':margin,'topologyChanged':False,'eyeGeometryChanged':False,'selections':selections,'movedVertices':len(movements),'maximumMoveM':max((m['lengthM'] for m in movements),default=0.),'movementRecords':movements,'lockedControlVertices':len(locked),'maximumLockedControlErrorM':max(((mesh.vertices[i].co-original[i]).length for i in locked),default=0.),'visibleLimitVerticesTested':len(visible_limit),'maximumFrontVisibleLimitMoveM':max(visible_limit,default=0.)}

variants=[]
for label,margin in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);body=bpy.data.objects['AFN_R0005_Body'];rig=bpy.data.objects['AFN_R0005_Rig'];parts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')];fits=eyes.helper_centres();set_pose(rig,'neutral');edit=repair(body,fits,margin)
    audits={};selfs={};renders=[]
    for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
        set_pose(rig,pose);audits[pose]=eyes.audit(body,parts);V,T,tree=evaluated(body);pairs=[(a,b) for a,b in tree.overlap(tree) if a<b and set(T[a]).isdisjoint(T[b])];selfs[pose]={'nonAdjacentTrianglePairs':len(pairs),'samplePairs':pairs[:8]}
        for view in (('face','oblique','profile','eyes') if pose=='neutral' else ('face','eyes')):renders.append(eyes.render(label,view,fits,pose))
    set_pose(rig,'neutral');scene['aevrynd_revision']='female-next-r0007-'+label;scene['aevrynd_release_state']='SOCKET_REPAIR_STUDY_NOT_PROMOTED';scene['aevrynd_website_promotion']='forbidden'
    output=SRC.parent/f'aevrynd-female-next-r0007-{label}-study.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output))
    neg=sum(p['negativeVertices'] for a in audits.values() for p in a.values());cross=sum(p['bodyTriangleIntersectionPairs'] for a in audits.values() for p in a.values());self_total=sum(x['nonAdjacentTrianglePairs'] for x in selfs.values())
    item={'label':label,'edit':edit,'poseAudit':audits,'bodySelfIntersectionAudit':selfs,'negativeObservations':neg,'bodyEyeCrossPairs':cross,'bodySelfPairs':self_total,'renders':renders,'output':str(output),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'technicalStatus':'PASS' if neg==0 and cross==0 and self_total==0 and edit['maximumFrontVisibleLimitMoveM']<=.00005 and edit['maximumLockedControlErrorM']==0 else 'FAIL'};variants.append(item)
    (E/'female-next-r0007-socket-clearance.report.json').write_text(json.dumps({'revision':'female-next-r0007','source':str(SRC),'variants':variants,'status':'VISUAL_REVIEW_PENDING','selectedVariant':None,'enginePromotionApproved':False,'websitePromotionApproved':False,'enginePerformance':{'status':'NOT_TESTED','cpuMs':None,'gpuMs':None,'memoryBytes':None},'scope':'Neutral, +/-10 degree gaze, +/-20 degree head turn. No blink or whole-character qualification.'},indent=2)+'\n')
    print('AFN_R0007='+json.dumps({'label':label,'editVertices':edit['movedVertices'],'maxMoveMm':edit['maximumMoveM']*1000,'visibleLimitMoveMm':edit['maximumFrontVisibleLimitMoveM']*1000,'negative':neg,'bodyEyePairs':cross,'bodySelfPairs':self_total,'status':item['technicalStatus']}),flush=True)
