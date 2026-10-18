"""Isolate eye-socket edits on a baked evaluated offline surface, retaining native source."""
import bpy,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0008-evaluated-sockets';E.mkdir(parents=True,exist_ok=True)
SRC=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0006-b-balanced-study.blend'
spec=importlib.util.spec_from_file_location('afn_socket_tools',Path(__file__).with_name('build-female-next-r0007-socket-clearance.py'));tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools);tools.eyes.E=E
VARIANTS=(('a-tight',.0003),('b-balanced',.0007),('c-reserved',.0012))

def bake_surface(body,rig):
    before,T,tree=tools.evaluated(body);groups=[g.name for g in body.vertex_groups]
    dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg);mesh.name='AFN_R0008_EvaluatedOfflineBody'
    body.data=mesh
    for name in groups:
        if body.vertex_groups.get(name) is None:body.vertex_groups.new(name=name)
    for m in list(body.modifiers):body.modifiers.remove(m)
    arm=body.modifiers.new('AFN_EvaluatedSurfaceSkinning','ARMATURE');arm.object=rig;body.name='AFN_R0008_Body'
    body['aevrynd_role']='Offline evaluated surface for constrained internal fitting; original low-resolution editable source retained separately'
    after,_,_=tools.evaluated(body)
    if len(before)!=len(after):raise RuntimeError('Bake changed vertex correspondence')
    error=max((a-b).length for a,b in zip(after,before))
    if error>1e-6:raise RuntimeError('Bake changed neutral surface')
    return before,tree,{'bakedVertices':len(mesh.vertices),'bakedPolygons':len(mesh.polygons),'maximumNeutralBakeErrorM':error,'runtimeLodStatus':'NOT_GENERATED','retainedEditableSource':'AFN_R0005_EditableNativeCC0'}

def repair_surface(body,rig,fits,margin,before,tree):
    mesh=body.data;centres={s:Vector(fits[s]['centre']) for s in ('L','R')};envelope={s:max((Vector(v.co)-centres[s]).length for obj in bpy.data.objects if obj.name.startswith('AFN6_'+s+'_') for v in obj.data.vertices) for s in ('L','R')};protected=[];free=[];movements=[]
    for i,p in enumerate(before):
        side=min(centres,key=lambda s:(p-centres[s]).length)
        if (p-centres[side]).length>.030:continue
        front=tree.ray_cast(Vector((p.x,-.4,p.z)),Vector((0.,1.,0.)),.5)[0];ey=tools.eye_front(p,centres[side],envelope[side])
        visible=front is not None and abs(front.y-p.y)<.00005 and (ey is None or p.y<ey-.0001)
        if visible:protected.append(i);continue
        free.append(i);delta=p-centres[side];target=envelope[side]+margin
        if delta.length>=target:continue
        q=centres[side]+delta.normalized()*target;move=q-p;mesh.vertices[i].co+=body.matrix_world.inverted().to_3x3()@move;movements.append({'vertex':i,'deltaM':list(move),'lengthM':move.length})
    mesh.update();after,_,_=tools.evaluated(body)
    return {'marginM':margin,'protectedFrontSurfaceVertices':protected,'freeSocketVertices':len(free),'movedVertices':len(movements),'maximumSocketMoveM':max((v['lengthM'] for v in movements),default=0.),'maximumProtectedFrontSurfaceMoveM':max(((after[i]-before[i]).length for i in protected),default=0.),'movementRecords':movements,'eyeGeometryChanged':False,'postBakeTopologyChanged':False}

variants=[]
for label,margin in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);rig=bpy.data.objects['AFN_R0005_Rig'];tools.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0005_Body'];fits=tools.eyes.helper_centres();parts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')]
    before,tree,bake=bake_surface(body,rig);edit=repair_surface(body,rig,fits,margin,before,tree);audits={};selfs={};renders=[]
    for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
        tools.set_pose(rig,pose);audits[pose]=tools.eyes.audit(body,parts);V,T,current=tools.evaluated(body);pairs=[(a,b) for a,b in current.overlap(current) if a<b and set(T[a]).isdisjoint(T[b])];selfs[pose]={'nonAdjacentTrianglePairs':len(pairs),'samplePairs':pairs[:8]}
        for view in (('face','oblique','profile','eyes') if pose=='neutral' else ('face','eyes')):renders.append(tools.eyes.render(label,view,fits,pose))
    tools.set_pose(rig,'neutral');scene['aevrynd_revision']='female-next-r0008-'+label;scene['aevrynd_release_state']='EVALUATED_SOCKET_STUDY_NOT_PROMOTED';scene['aevrynd_website_promotion']='forbidden'
    output=SRC.parent/f'aevrynd-female-next-r0008-{label}-study.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output))
    neg=sum(v['negativeVertices'] for a in audits.values() for v in a.values());cross=sum(v['bodyTriangleIntersectionPairs'] for a in audits.values() for v in a.values());selfcount=sum(a['nonAdjacentTrianglePairs'] for a in selfs.values());item={'label':label,'bake':bake,'edit':edit,'poseAudit':audits,'bodySelfIntersectionAudit':selfs,'negativeObservations':neg,'bodyEyeCrossPairs':cross,'bodySelfPairs':selfcount,'output':str(output),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'renders':renders,'nearestNormalDiagnosticStatus':'NO_NEGATIVE_FLAGS' if neg==0 else 'NEGATIVE_FLAGS_REQUIRE_CONTAINMENT','technicalStatus':'PENDING_CLOSED_SOLID_VERIFICATION'};variants.append(item)
    (E/'female-next-r0008-evaluated-sockets.report.json').write_text(json.dumps({'revision':'female-next-r0008','source':str(SRC),'variants':variants,'selectedVariant':None,'status':'VISUAL_REVIEW_PENDING','enginePromotionApproved':False,'websitePromotionApproved':False,'enginePerformance':{'status':'NOT_TESTED','cpuMs':None,'gpuMs':None,'memoryBytes':None},'scope':'Offline evaluated body. Neutral, +/-10 degree gaze, +/-20 degree head turn only; no blink or full-character qualification.'},indent=2)+'\n')
    print('AFN_R0008='+json.dumps({'label':label,'movedVertices':edit['movedVertices'],'maxMoveMm':edit['maximumSocketMoveM']*1000,'protectedMoveMm':edit['maximumProtectedFrontSurfaceMoveM']*1000,'negative':neg,'bodyEyePairs':cross,'bodySelfPairs':selfcount,'bytes':item['bytes'],'status':item['technicalStatus']}),flush=True)
