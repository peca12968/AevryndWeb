"""One complete woman: source-indexed FK skinning and live render-scalp frames.

This is attachment, never a hair dynamics or collision solver.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time,math,sys,importlib.util
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
def module(name,file):
    sp=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
base=module('rig69base','build-female-next-r0068-guide-surface.py');k=base.k;shade=base.shade
R=base.R;E=R/'Evidence/character-female-next/r0069-complete-controls';D=R/'Reference/character/charmorph-vitruvian-cc0/r0069-rig-data';S=base.S;SRC=S/'aevrynd-female-next-r0068-c-live-body-contact-study.blend';OUT=S/'aevrynd-female-next-r0069-a-complete-controls-study.blend';SOURCE_SHA='ee588d13ef05eb7d54c231bc3438bde2653133dc4a739889da7e5ab5b9bf2dcc'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(E/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def native_names():return list(read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values())
def unpack(path):
    z=np.load(path,allow_pickle=False);names=z['names'].item().decode().split('\0');offset=0;out={}
    assert len(names)==len(z['cnt'])
    for name,count in zip(names,z['cnt']):
        count=int(count);out[name]=(z['idx'][offset:offset+count],z['weights'][offset:offset+count]);offset+=count
    assert offset==len(z['idx']);return out
def attr(d,name,kind,domain,data):
    a=d.attributes.new(name,kind,domain);a.data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.asarray(data).ravel())
def make_rig(V):
    with bpy.data.libraries.load(str(D/'rigs.blend'),link=False) as (src,dst):dst.objects=['mixamo_vitruvian']
    template=dst.objects[0];joints={n:np.average(V[ids],axis=0,weights=w) for n,(ids,w) in unpack(D/'joints/Mixamo.npz').items()};records=[]
    for b in template.data.bones:records.append({'old':b.name,'name':b.name.removeprefix('mixamorig:'),'parent':b.parent.name.removeprefix('mixamorig:') if b.parent else None,'connected':b.use_connect,'z':b.matrix_local.to_3x3().col[2].copy()})
    data=bpy.data.armatures.new('AFN69_SOURCE_INDEXED_BODY_BONES');rig=bpy.data.objects.new('AFN69_BODY_CONTROLS',data);bpy.context.scene.collection.objects.link(rig);rig.show_in_front=True;rig.data.display_type='OCTAHEDRAL'
    for o in bpy.context.selected_objects:o.select_set(False)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');done={}
    for row in records:
        b=data.edit_bones.new(row['name']);h=joints.get('joint_'+row['old']+'_head');t=joints.get('joint_'+row['old']+'_tail');assert t is not None
        if h is None:assert row['connected'] and row['parent'] in done;h=done[row['parent']].tail[:]
        b.head=h;b.tail=t;assert b.length>.0001;b.align_roll(row['z']);b.use_deform=True
        if row['parent']:b.parent=done[row['parent']];b.use_connect=row['connected']
        done[row['name']]=b
    bpy.ops.object.mode_set(mode='OBJECT');assert len(data.bones)==52
    weights=unpack(D/'weights/mixamo.npz');W=np.zeros((37436,52),'f8');order=[b.name for b in data.bones];index={n:i for i,n in enumerate(order)}
    for old,(ids,w) in weights.items():W[ids,index[old.removeprefix('mixamorig:')]]=w
    sums=W.sum(1);assert sums.min()>0 and np.isfinite(W).all() and (W>=0).all();W/=sums[:,None];np.savez_compressed(E/'source-indexed-body-weights.npz',weights=W.astype('f4'),names=np.array(order))
    rig['scope']='52 source-indexed CC0 FK bones, morphology-fitted from native joint landmarks. No addon/remote service; no complete animation/contact acceptance.'
    return rig,W,order,{'bones':len(order),'sourceWeightSumRange':[float(sums.min()),float(sums.max())],'normalizationOnlyNotWeightRetuning':True,'sourceJointRecords':len(joints)}
def skin(o,rig,W,order,ids):
    for i,name in enumerate(order):
        weights=W[ids,i];active=np.flatnonzero(weights>0)
        if len(active):
            vg=o.vertex_groups.get(name) or o.vertex_groups.new(name=name)
            for v in active:vg.add([int(v)],float(weights[v]),'REPLACE')
    md=o.modifiers.new('AFN69_SOURCE_INDEXED_SKIN','ARMATURE');md.object=rig;md.use_deform_preserve_volume=False
    bpy.context.view_layer.objects.active=o
    while list(o.modifiers).index(md)>0:bpy.ops.object.modifier_move_up(modifier=md.name)
def frames(tri):
    a=tri[:,1]-tri[:,0];a/=np.linalg.norm(a,axis=1)[:,None];n=np.cross(a,tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1)[:,None];b=np.cross(n,a);return a,b,n
def follower(o,body,rest_body,row,tree):
    d=o.data;counts=np.array([c.points_length for c in d.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];P=base.array3(d.position_data,'vector').astype('f8');A=np.array(o.matrix_world);assert np.allclose(A[:3,:3],np.diag(np.diag(A[:3,:3])));world=P@A[:3,:3].T+A[:3,3];ids=[];bary=[];gaps=[]
    for root in world[starts]:
        co,_,i,gap=tree.find_nearest(Vector(root));ids.append(row['T'][i]);bary.append(base.bary(np.array(co),row['V'][row['T'][i]]));gaps.append(gap)
    ids=np.array(ids,'i4');bary=np.array(bary);tri=row['V'][ids];anchor=np.einsum('ij,ijk->ik',bary,tri);t,b,n=frames(tri)
    for j in range(3):attr(d,'AFN69_BodyVertex'+str(j),'INT','CURVE',ids[:,j])
    for name,value in [('Barycentric',bary),('RestAnchor',anchor),('RestTangent',t),('RestBinormal',b),('RestNormal',n)]:attr(d,'AFN69_'+name,'FLOAT_VECTOR','CURVE',value.astype('f4'))
    ng=bpy.data.node_groups.new(o.name+'_ACTUAL_SCALP_FRAME','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=ng.nodes;links=ng.links
    inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput');info=nodes.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=body;info.inputs['As Instance'].default_value=False;pos=nodes.new('GeometryNodeInputPosition')
    def vec(op,*args):
        node=nodes.new('ShaderNodeVectorMath');node.operation=op
        for i,arg in enumerate(args):
            socket=node.inputs[3] if op=='SCALE' and i==1 else node.inputs[i]
            if hasattr(arg,'node'):links.new(arg,socket)
            else:socket.default_value=arg
        return node.outputs['Value'] if op in ('DOT_PRODUCT','DISTANCE','LENGTH') else node.outputs['Vector']
    def named(name,kind='FLOAT_VECTOR'):
        a=nodes.new('GeometryNodeInputNamedAttribute');a.data_type=kind;a.inputs['Name'].default_value='AFN69_'+name;return a.outputs['Attribute']
    scale=np.diag(A[:3,:3]).tolist();translation=A[:3,3].tolist()
    def to_world(p):return vec('ADD',vec('MULTIPLY',p,scale),translation)
    Pworld=to_world(pos.outputs['Position']);restinfo=nodes.new('GeometryNodeObjectInfo');restinfo.transform_space='RELATIVE';restinfo.inputs['Object'].default_value=rest_body;restinfo.inputs['As Instance'].default_value=False
    sep=nodes.new('ShaderNodeSeparateXYZ');links.new(named('Barycentric'),sep.inputs[0])
    def sampled_frame(geometry):
        local_points=[]
        for i in range(3):
            sample=nodes.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;links.new(geometry,sample.inputs['Geometry']);links.new(pos.outputs['Position'],sample.inputs['Value']);links.new(named('BodyVertex'+str(i),'INT'),sample.inputs['Index']);local_points.append(sample.outputs['Value'])
        pts=[to_world(p) for p in local_points];edge1=vec('MULTIPLY',vec('SUBTRACT',local_points[1],local_points[0]),scale);edge2=vec('MULTIPLY',vec('SUBTRACT',local_points[2],local_points[0]),scale);tangent=vec('NORMALIZE',edge1);normal=vec('NORMALIZE',vec('CROSS_PRODUCT',tangent,edge2));binormal=vec('CROSS_PRODUCT',normal,tangent);anchor=vec('ADD',vec('ADD',vec('SCALE',pts[0],sep.outputs[0]),vec('SCALE',pts[1],sep.outputs[1])),vec('SCALE',pts[2],sep.outputs[2]));return anchor,(tangent,binormal,normal)
    anchor_now,current_basis=sampled_frame(info.outputs['Geometry']);rest_anchor,rest_basis=sampled_frame(restinfo.outputs['Geometry']);offset=vec('SUBTRACT',Pworld,rest_anchor);world_now=anchor_now
    for basis,current in zip(rest_basis,current_basis):world_now=vec('ADD',world_now,vec('SCALE',current,vec('DOT_PRODUCT',offset,basis)))
    local=vec('DIVIDE',vec('SUBTRACT',world_now,translation),scale);setpos=nodes.new('GeometryNodeSetPosition');links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);links.new(local,setpos.inputs['Position']);links.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=o.modifiers.new('AFN69_LIVE_RENDER_SCALP_FRAME','NODES');md.node_group=ng
    o['AFN69_scope']='Per-strand rest render triangle/barycentric and world orthonormal frame, sampled from actual deformed body. Entire strand follows its root frame rigidly; no inertia, collision, bending or torsion solver. Original radius/material/matrix retained.'
    np.savez_compressed(E/(o.name+'-binding.npz'),ids=ids,bary=bary,anchor=anchor,tangent=t,binormal=b,normal=n,starts=starts,counts=counts,restWorld=world,matrix=A)
    return {'object':o.name,'curves':len(counts),'points':len(P),'restRootSurfaceDistanceRangeM':[float(min(gaps)),float(max(gaps))],'binding':'Actual render-body triangle vertices + barycentric / world orthonormal frame','noHairPhysics':True}
def axis_pose(rig,bone,axis,degrees):
    p=rig.pose.bones[bone];p.rotation_mode='QUATERNION';local=p.bone.matrix_local.to_3x3().transposed()@Vector(axis);p.rotation_quaternion=Quaternion(local,math.radians(degrees))
def animate(rig):
    timeline=[(1,0,0,0),(13,-20,0,0),(25,20,0,0),(37,0,0,0),(49,0,-35,25),(61,0,0,0)]
    for f,yaw,left,right in timeline:
        for n,ax,value in [('Head',(0,0,1),yaw),('LeftArm',(0,1,0),left),('RightArm',(0,1,0),right)]:axis_pose(rig,n,ax,value);rig.pose.bones[n].keyframe_insert(data_path='rotation_quaternion',frame=f)
    action=rig.animation_data.action;action.name='AFN69_CONTROLLED_HEAD_TURN_AND_ARM_RAISE'
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for p in fc.keyframe_points:p.interpolation='LINEAR'
    s=bpy.context.scene;s.frame_start=1;s.frame_end=61;s.render.fps=24;return timeline
def preview():
    shade.settings();s=bpy.context.scene;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;rows=[]
    for f,view in ((25,'face'),(49,'body-face')):
        s.frame_set(f);k.b.camera(view);s.camera.data.lens=85;s.render.filepath=str(E/f'a-pilot-{f}-{view}.png');bpy.ops.render.render(write_still=True);rows.append({'frame':f,'view':view,'file':s.render.filepath,'resolution':640,'samples':16,'camera':np.array(s.camera.matrix_world).tolist()})
    s.frame_set(1);save('a-pilot-controls.json',rows)
def main():
    tick=time.time()
    if '--preview' in sys.argv:
        assert sha(OUT)==read(E/'a-build-summary.json')['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));preview();return
    assert not OUT.exists() and sha(SRC)==SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();names=native_names()
    for o in bpy.data.objects:
        if o.type=='MESH':
            for md in o.modifiers:
                if md.type=='SUBSURF':md.levels=md.render_levels
    old={n:k.mesh(bpy.data.objects[n])['V'] for n in names};oldcurves={n:base.array3(bpy.data.objects[n].evaluated_get(bpy.context.evaluated_depsgraph_get()).data.position_data,'vector') for n in ('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES')};V=np.load(E/'native-rest-world.npy');rig,W,order,rig_summary=make_rig(V)
    ctrl=bpy.data.objects['AFN59_FACE_CONTROLS'];old_action=ctrl.animation_data.action;old_action.use_fake_user=True;ctrl.animation_data.action=None;ctrl['blink_left']=ctrl['blink_right']=0.;ctrl['AFN69_original_blink_action']=old_action.name
    for name in names:
        o=bpy.data.objects[name];ids=np.empty(len(o.data.vertices),'i4');o.data.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids);skin(o,rig,W,order,ids)
    from mathutils.kdtree import KDTree
    kd=KDTree(len(V))
    for i,p in enumerate(V):kd.insert(p,i)
    kd.balance();facial=[]
    for name in ('AFN59_LASHES_NATIVE_POINT_POSES','AFN59_BROWS_NATIVE_POINT_POSES'):
        o=bpy.data.objects[name];P=base.array3(o.data.vertices,'co');A=np.array(o.matrix_world);world=P@A[:3,:3].T+A[:3,3];ids=np.array([kd.find(Vector(p))[1] for p in world]);skin(o,rig,W,order,ids);facial.append({'object':name,'points':len(ids),'weights':'Nearest corresponding actual native neutral cage point; blink keys precede skinning, display curves sample evaluated point helper. Not exact follicle/root acceptance.'})
    scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects[names[4]];row=k.mesh(body);tree=BVHTree.FromPolygons(row['V'].tolist(),row['T'].tolist(),all_triangles=True);bindings=[]
    evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;points=base.array3(evaluated.vertices,'co');rest_mesh=bpy.data.meshes.new('AFN69_REST_BODY_POINT_REFERENCE');rest_mesh.vertices.add(len(points));rest_mesh.vertices.foreach_set('co',points.ravel());rest_mesh.update();rest_body=bpy.data.objects.new(rest_mesh.name,rest_mesh);bpy.context.scene.collection.objects.link(rest_body);rest_body.matrix_world=body.matrix_world.copy();rest_body.hide_render=True;rest_body.hide_set(True);rest_body['scope']='Position-only rest reference for identical Geometry Nodes frame arithmetic; no faces, no collision surface, no dynamic proxy.'
    for name in oldcurves:bindings.append(follower(bpy.data.objects[name],body,rest_body,row,tree))
    timeline=animate(rig);scene.frame_set(1);bpy.context.view_layer.update();neutral={n:float(np.linalg.norm(k.mesh(bpy.data.objects[n])['V']-old[n],axis=1).max()) for n in names};assert max(neutral.values())<1e-6,neutral
    hair_error={}
    for name,P in oldcurves.items():
        o=bpy.data.objects[name];Q=base.array3(o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.position_data,'vector');A=np.array(o.matrix_world)[:3,:3];hair_error[name]=float(np.linalg.norm((Q-P)@A.T,axis=1).max())
    assert max(hair_error.values())<1e-6,hair_error
    scene['AFN69_scope']='Source-indexed52-bone FK plus actual render-scalp frame following on complete woman. Head/arm authored pilot action. Rigid per-strand root-frame transport is NOT natural hair dynamics or collision acceptance.';rig['instructions']='Pose Mode: select Head, Neck, spine or limb/finger bones. Play1-61 for controlled head turn and arm raise. Facial blink properties remain on AFN59_FACE_CONTROLS; old blink action retained but detached during this control demonstration.'
    for o in bpy.context.selected_objects:o.select_set(False)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig;k.b.camera('face');scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save('a-build-summary.json',{'revision':'female-next-r0069','source':str(SRC),'sourceSha256':SOURCE_SHA,'output':str(OUT),'outputSha256':sha(OUT),'rig':rig_summary,'boneObject':rig.name,'timeline':timeline,'fps':24,'skinMethod':'Linear blend skinning, normalized source-indexed weights, armature before unchanged subdivision/lining deletion. No auto-weight solve or parameter sweep.','facialPointHelpers':facial,'visibleGroomFollowing':bindings,'neutralBodyMaximumWorldErrorsM':neutral,'neutralHairMaximumWorldErrorsM':hair_error,'oldBlinkActionRetainedDetachedForControlPilot':old_action.name,'sourceNativeMeshKeysUVMaterialsAndHairRadiiUnedited':True,'hiddenAuthoringGrowthAndGuidesStillNeutralOnly':True,'newHairPhysicsOrContactsOrRuntimeAccepted':False,'sourceCredits':'Rig/weights/joints Vitruvian CC0; r68 hairstyle retains Daniel Bystedt CC BY-SA notice, version unspecified; no third-party software code or paid service used.','secondsBeforePreview':time.time()-tick})
    print('R69_COMPLETE_SOURCE_SAVED',neutral,hair_error,time.time()-tick,flush=True);preview();print('R69_PILOT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
