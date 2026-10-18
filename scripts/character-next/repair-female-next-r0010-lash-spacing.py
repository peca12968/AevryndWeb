"""Final bounded candidate: relocate clumped roots onto skin rows with collision tests."""
import bpy,json,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0010-eye-rim'; S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('rim',Path(__file__).with_name('build-female-next-r0010-eye-rim.py'))
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
SRC=S/'aevrynd-female-next-r0010-b-organic-lashes-study.blend'
bpy.ops.wm.open_mainfile(filepath=str(SRC)); body=bpy.data.objects['AFN_R0008_Body']; rig=bpy.data.objects['AFN_R0005_Rig']; builder.stage.set_pose(rig,'neutral'); body.data.calc_loop_triangles()
V=[body.matrix_world@v.co for v in body.data.vertices]; T=[tuple(t.vertices) for t in body.data.loop_triangles]; bodytree=BVHTree.FromPolygons(V,T,all_triangles=True)
optics=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith('AFN6_'):
        o.data.calc_loop_triangles();optics.append(BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True))
bindings=json.loads((E/'b-organic-lashes-lash-bindings.json').read_text()); kept=[]; edits=[]; removed=[]
for obj in sorted((o for o in bpy.data.objects if o.name.startswith('AFN10_') and o.type=='MESH'),key=lambda o:o.name):
    old=obj.data; old.calc_loop_triangles(); final_v=[]; final_f=[]; final_weights=[]; accepted=None; current=[x for x in bindings if x['object']==obj.name]; zsign=1 if 'upper' in obj.name else -1
    for hair in current:
        start=hair['firstVertex']; oldp=[old.vertices[start+i].co.copy() for i in range(66)]; oldroot=sum(oldp[:6],Vector())/6.; local_faces=[tuple(v-start for v in p.vertices) for p in old.polygons if all(start<=v<start+66 for v in p.vertices)]
        attempts=[(x*zsign,z*zsign) for z in (0.,.00012,.00024) for x in (0.,-.00010,.00010,-.00020,.00020,-.00032,.00032,-.00045,.00045)]
        chosen=None
        for dx,dz in attempts:
            if dx==dz==0:
                P=oldp; delta=Vector(); hit=builder.front(bodytree,oldroot.x,oldroot.z)[0]
            else:
                hit,n,ti,d=builder.front(bodytree,oldroot.x+dx,oldroot.z+dz)
                if hit is None or hit.y>-.115:continue
                newroot=hit+n*(hair['radiusM']+.000025); delta=newroot-oldroot
                if delta.length>.0008:continue
                P=[p+delta for p in oldp]
            trial=BVHTree.FromPolygons(P,local_faces,epsilon=.000002)
            if bodytree.overlap(trial) or any(t.overlap(trial) for t in optics) or (accepted and accepted.overlap(trial)):continue
            chosen=(P,delta,hit,dx,dz);break
        if chosen is None:
            removed.append({'object':obj.name,'hair':hair['hair'],'reason':'No collision-free skin-row root among 27 bounded alternatives'});continue
        P,delta,_,dx,dz=chosen; newroot=sum(P[:6],Vector())/6.; nearest=bodytree.find_nearest(newroot); hit,n,ti,d=nearest
        ids=list(T[ti]); bc=builder.barycentric(hit,*[V[i] for i in ids]); groups={}
        for vi,w in zip(ids,bc):
            for g in body.data.vertices[vi].groups:
                name=body.vertex_groups[g.group].name
                if name in rig.data.bones:groups[name]=groups.get(name,0)+w*g.weight
        total=sum(groups.values());groups={k:v/total for k,v in groups.items() if v>1e-8}
        offset=len(final_v); final_v+=P; final_f += [tuple(offset+i for i in f) for f in local_faces];final_weights += [groups]*66
        row={**hair,'firstVertex':offset,'sourceHair':hair['hair'],'hair':offset//66,'bodyTriangle':ti,'bodyVertices':ids,'barycentric':bc,'root':list(newroot),'boneWeights':groups,'rootSurfaceGapM':d}
        kept.append(row); edits.append({'object':obj.name,'hair':hair['hair'],'deltaM':list(delta),'lengthM':delta.length,'rowDxM':dx,'rowDzM':dz})
        accepted=BVHTree.FromPolygons(final_v,final_f,epsilon=.000002)
    mesh=bpy.data.meshes.new(obj.name+'-spaced');mesh.from_pydata(final_v,[],final_f);mesh.update();mesh.materials.append(old.materials[0]); obj.data=mesh
    obj.vertex_groups.clear(); names=sorted({name for row in final_weights for name in row}); vg={name:obj.vertex_groups.new(name=name) for name in names}
    for i,row in enumerate(final_weights):
        for name,w in row.items():vg[name].add([i],w,'REPLACE')
    for p in mesh.polygons:p.use_smooth=True
    obj['aevrynd_root_binding']='c-spaced-lashes-lash-bindings.json'; obj['aevrynd_revision']='female-next-r0010-c-spaced-lashes'
    print('AFN_R0010_SPACING='+json.dumps({'object':obj.name,'keptHairs':len(final_v)//66,'removed':len(current)-len(final_v)//66}),flush=True)
assert len(kept)>=198, 'More than 10% pruning is not acceptable for this study'
(E/'c-spaced-lashes-lash-bindings.json').write_text(json.dumps(kept,indent=2)+'\n')
(E/'c-root-spacing.json').write_text(json.dumps({'method':'Greedy exact triangle collision rejection with 2um BVH margin; up to 27 skin-projected root-row translations per strand. No intersection exclusions.','edits':edits,'removed':removed},indent=2)+'\n')
images=[builder.stage.render('c-spaced-lashes',v,builder.stage.helper_centres(),'neutral') for v in ('eyes','face','oblique')]
scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0010-c-spaced-lashes';scene['aevrynd_release_state']='EYE_RIM_STUDY_PENDING_COLLISION_AND_VISUAL_REVIEW'
dest=S/'aevrynd-female-next-r0010-c-spaced-lashes-study.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
report=json.loads((E/'female-next-r0010-b-organic-lashes.report.json').read_text());report.update({'variant':'c-spaced-lashes','output':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'repairInput':str(SRC),'repairInputSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'renders':images,'spacingEdits':sum(x['lengthM']>0 for x in edits),'removedHairs':len(removed),'status':'PENDING_TECHNICAL_VISUAL_REVIEW'})
report['lashes'].update({'hairs':len(kept),'vertices':sum(len(bpy.data.objects[n].data.vertices) for n in report['lashes']['objects']),'triangles':sum(sum(len(f.vertices)-2 for f in bpy.data.objects[n].data.polygons) for n in report['lashes']['objects'])})
(E/'female-next-r0010-c-spaced-lashes.report.json').write_text(json.dumps(report,indent=2)+'\n')
print('AFN_R0010_SPACING_DONE')
