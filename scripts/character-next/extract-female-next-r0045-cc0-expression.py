"""Extract CC0 authored face-unit motion using the already installed MPFB.

MPFB is an offline Blender production tool only. No GPL implementation is
copied into the engine. BVH parsing and data-only skinning below are our own.
Output is a registered-motion reference, not a replacement female character.
"""
import bpy,json,re,time,hashlib,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0045-closed-lid-topology';REF=R/'Reference/character/makehuman-face-units-cc0'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse():
    text=(REF/'face-poseunits.bvh').read_text();header,motion=text.split('MOTION');lines=header.splitlines();stack=[];records=[];latest=None;end=False;offset=0
    for line in lines:
        tokens=line.split()
        if not tokens:continue
        if tokens[0] in ('ROOT','JOINT'):
            latest={'name':tokens[1],'parent':stack[-1]['name'] if stack and stack[-1] is not None else None};records.append(latest);end=False
        elif tokens[0]=='End':latest=None;end=True
        elif tokens[0]=='{':stack.append(latest)
        elif tokens[0]=='}':stack.pop()
        elif tokens[0]=='CHANNELS':
            assert stack[-1] is not None;stack[-1]['channels']=tokens[2:];stack[-1]['channelStart']=offset;offset+=int(tokens[1])
    ls=motion.strip().splitlines();count=int(ls[0].split(':')[1]);data=np.array([[float(v) for v in l.split()] for l in ls[2:] if l.strip()]);assert data.shape==(count,offset);return records,data
def rot(axis,angle):
    c,s=np.cos(angle),np.sin(angle)
    return {'X':np.array(((1,0,0),(0,c,-s),(0,s,c))),'Y':np.array(((c,0,s),(0,1,0),(-s,0,c))),'Z':np.array(((c,-s,0),(s,c,0),(0,0,1)))}[axis]
def main():
    tick=time.time();meta=json.loads((REF/'face-poseunits.json').read_text());assert meta['license']=='CC0';rec,data=parse();bpy.ops.wm.read_factory_settings(use_empty=True)
    import bl_ext.user_default.mpfb as mpfb
    mpfb.MPFB_CONTEXTUAL_INFORMATION={'__package__':str(mpfb.__package__),'__package_short__':str(mpfb.__package__).split('.')[-1],'__file__':str(mpfb.__file__)}
    prefs={'mpfb_shelf_label':'MPFB','mpfb_user_data':'','mpfb_second_root':'','mh_user_data':'','mh_auto_user_data':False};mpfb.get_preference=lambda n:prefs.get(n)
    from bl_ext.user_default.mpfb.services import HumanService,TargetService
    macro=TargetService.get_default_macro_info_dict();macro.update(gender=.04,age=.47,muscle=.43,weight=.48,height=.50,proportions=.52,cupsize=.43,firmness=.42);macro['race'].update(african=.24,asian=.42,caucasian=.34)
    human=HumanService.create_human(mask_helpers=True,detailed_helpers=True,extra_vertex_groups=True,feet_on_ground=True,scale=.1,macro_detail_dict=macro);human.name='AFN45_CC0_FEMALE_EXPRESSION_REFERENCE';rig=HumanService.add_builtin_rig(human,'default',import_weights=True);bpy.context.view_layer.update();assert rig
    # Keep original native indexing for data-only weight application. Helpers
    # remain excluded from the reference render, not from stored mesh indexing.
    flags=[(m,m.show_viewport) for m in human.modifiers]
    for m,_ in flags:m.show_viewport=False
    bpy.context.view_layer.update();ev=human.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();P=np.empty(len(mesh.vertices)*3,dtype='f4');mesh.vertices.foreach_get('co',P);P=P.reshape(-1,3).astype('f8');mx=np.array(human.matrix_world);P=P@mx[:3,:3].T+mx[:3,3];ev.to_mesh_clear();heads={bone.name:np.array(rig.matrix_world@bone.head_local) for bone in rig.data.bones};boneParents={bone.name:bone.parent.name if bone.parent else None for bone in rig.data.bones};channels={r['name']:r for r in rec};basis={};used=[]
    units=['LeftUpperLidClosed','RightUpperLidClosed','LeftLowerLidUp','RightLowerLidUp'];unitWeights=[1.,1.,.20,.20];indices=[meta['framemapping'].index(n) for n in units]
    for record in rec:
        name=record['name'];M=np.eye(3);rr=record['channelStart'];angles=[]
        for j,ch in enumerate(record['channels']):
            if ch.endswith('rotation'):
                angle=float(sum(w*(data[k,rr+j]-data[0,rr+j]) for k,w in zip(indices,unitWeights)));angle=0. if abs(angle)<.0001 else angle;M=M@rot(ch[0],np.radians(angle));angles.append(angle)
        basis[name]=M
        if np.linalg.norm(M-np.eye(3))>1e-8:used.append({'bone':name,'channels':record['channels'],'combinedAnglesDegrees':angles,'existsInFittedRig':name in heads})
    assert all(x['existsInFittedRig'] for x in used);transforms={}
    def transform(name,amount):
        if name in transforms:return transforms[name]
        record=channels.get(name);parent=boneParents[name];G=np.eye(4)
        if parent:G=transform(parent,amount).copy();G[:3,3]+=G[:3,:3]@(heads[name]-heads[parent])
        else:G[:3,3]=heads[name]
        if record:
            L=np.eye(3);start=record['channelStart']
            for j,ch in enumerate(record['channels']):
                if ch.endswith('rotation'):
                    angle=float(sum(w*(data[k,start+j]-data[0,start+j]) for k,w in zip(indices,unitWeights)));angle=0. if abs(angle)<.0001 else angle;L=L@rot(ch[0],np.radians(amount*angle))
            G[:3,:3]=G[:3,:3]@L
        transforms[name]=G;return G
    weights={g.index:g.name for g in human.vertex_groups};arrays={}
    for amount in (.5,1.):
        transforms={};out=np.zeros_like(P);total=np.zeros(len(P))
        for vertex in human.data.vertices:
            vi=vertex.index
            for group in vertex.groups:
                name=weights[group.group]
                if name not in heads:continue
                G=transform(name,amount);q=G[:3,:3]@(P[vi]-heads[name])+G[:3,3];out[vi]+=group.weight*q;total[vi]+=group.weight
        ok=total>1e-8;out[ok]/=total[ok,None];out[~ok]=P[~ok];arrays[f'closed{amount}']=out
    for m,flag in flags:m.show_viewport=flag
    # Bake the generated reference shape onto native vertices after clearing
    # production-tool modifiers/keys, retaining helper mask for visibility.
    maskmods=[m for m in human.modifiers if m.type=='MASK']
    for m in list(human.modifiers):
        if m.type!='MASK':human.modifiers.remove(m)
    human.shape_key_clear()
    local=(P-np.array(human.matrix_world)[:3,3])@np.linalg.inv(np.array(human.matrix_world)[:3,:3]).T;human.data.vertices.foreach_set('co',local.astype('f4').ravel());human.data.update();human.shape_key_add(name='Basis')
    k=human.shape_key_add(name='CC0_AUTHORED_UPPER_LIDS_CLOSED');q=(arrays['closed1.0']-np.array(human.matrix_world)[:3,3])@np.linalg.inv(np.array(human.matrix_world)[:3,:3]).T;k.data.foreach_set('co',q.astype('f4').ravel())
    human.data.calc_loop_triangles();fullT=np.array([t.vertices[:] for t in human.data.loop_triangles],dtype='i4');gp=json.loads((Path(mpfb.__file__).parent/'data/mesh_metadata/basemesh_vertex_groups.json').read_text());helperT={}
    for side in ('L','R'):
        ids=np.concatenate([np.arange(start,end+1) for start,end in gp['helper-'+side.lower()+'-eye']]);helperT['helperEyeTriangles'+side]=fullT[np.all(np.isin(fullT,ids),axis=1)]
    indexAttr=human.data.attributes.new('AFN45_ReferenceNativeIndex','INT','POINT');indexAttr.data.foreach_set('value',np.arange(len(P),dtype='i4'));bpy.context.view_layer.update();he=human.evaluated_get(bpy.context.evaluated_depsgraph_get());hm=he.to_mesh();hm.calc_loop_triangles();index=np.empty(len(hm.vertices),dtype='i4');hm.attributes['AFN45_ReferenceNativeIndex'].data.foreach_get('value',index);T=index[np.array([t.vertices[:] for t in hm.loop_triangles],dtype='i4')];he.to_mesh_clear();np.savez_compressed(E/'b-cc0-authored-closed-reference.npz',restWorld=P,halfWorld=arrays['closed0.5'],closedWorld=arrays['closed1.0'],triangles=T,eyeCenterL=heads['eye.L'],eyeCenterR=heads['eye.R'],**helperT)
    mat=bpy.data.materials.new('reference_only_clay');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.24,.20,1);bs.inputs['Roughness'].default_value=.6;human.data.materials.clear();human.data.materials.append(mat)
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;s.world=bpy.data.worlds.new('cc0_motion_reference');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.08,.08,.08,1)
    center=(heads['eye.L']+heads['eye.R'])*.5;cam=bpy.data.objects.new('reference_camera',bpy.data.cameras.new('reference_camera'));s.collection.objects.link(cam);s.camera=cam;cam.location=Vector(center)+Vector((0,-.70,.025));target=Vector(center)+Vector((0,0,-.015));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=85
    for name,pos,power,size in [('key',(-.4,-.5,.5),70.,.4),('fill',(.4,-.3,.1),30.,.4)]:
        o=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));s.collection.objects.link(o);o.location=Vector(center)+Vector(pos);o.rotation_euler=(Vector(center)-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.shape='DISK';o.data.size=size
    if '--data-only' not in sys.argv:
        for value,tag in [(0,'open'),(1,'closed')]:k.value=value;bpy.context.view_layer.update();s.render.filepath=str(E/f'b-cc0-reference-{tag}.png');bpy.ops.render.render(write_still=True)
    save('b-cc0-expression-extraction.json',{'status':'REFERENCE_MOTION_REQUIRES_GEOMETRIC_FIDELITY_REVIEW','dataLicense':'CC0','poseUnitsSource':json.loads((REF/'PROVENANCE.json').read_text(encoding='utf-8-sig')),'units':units,'unitWeights':unitWeights,'frames':indices,'rotationDataNoiseFloorDegrees':.0001,'movingBones':used,'nativeVertices':len(P),'visibleSkinNativeIndices':int(len(np.unique(T))),'eyeCenters':{n:heads[n].tolist() for n in ['eye.L','eye.R']},'maximumDisplacementM':float(np.linalg.norm(arrays['closed1.0']-P,axis=1).max()),'method':'Own BVH channel parser and global-joint skinning using fitted installed MPFB rig/CC0weights; fitted rest offsets, BVH rotation axes treated as Blender world-axis reference. Closure composition is upper1+lower0.2, an explicit authoring choice, not captured/blink timing data. Tiny file quantization rotations below0.0001degree are treated as zero, not a contact tolerance. Must validate reference geometry before transfer. No external runtime code copied.','use':'Female motion/topology reference only, not a new working character or own scan-face improvement','seconds':time.time()-tick});print('R45_CC0_MOTION_REFERENCE',len(P),used,time.time()-tick,flush=True)
if __name__=='__main__':main()
