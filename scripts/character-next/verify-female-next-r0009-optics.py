"""Reopen the saved candidate and prove exact collision-relevant state inheritance."""
import bpy, array, hashlib, json, math
from pathlib import Path
R=Path(r'D:\Download\Aevrynd'); E=R/'Evidence/character-female-next/r0009-optics'
S=R/'engine/assets/characters/female-next/source'
BASE=S/'aevrynd-female-next-r0008-a-tight-study.blend'
CAND=S/'aevrynd-female-next-r0009-a-slab-thickness-study.blend'

def floats(data):
    return hashlib.sha256(array.array('f',data).tobytes()).hexdigest()

def scalars(obj):
    return {p.identifier:getattr(obj,p.identifier) for p in obj.bl_rna.properties
            if p.type in {'BOOLEAN','INT','FLOAT','ENUM','STRING'} and not getattr(p,'is_array',False) and p.identifier not in {'name','name_full','session_uid'}}

def meshes():
    result={}
    for o in bpy.data.objects:
        if o.type!='MESH': continue
        m=o.data; h=hashlib.sha256()
        for field,container,kind,n in [('co',m.vertices,'f',3),('vertex_index',m.loops,'i',1),('loop_start',m.polygons,'i',1),('loop_total',m.polygons,'i',1)]:
            a=array.array(kind,[0]*(len(container)*n)); container.foreach_get(field,a); h.update(a.tobytes())
        for uv in m.uv_layers:
            a=array.array('f',[0.]*(len(uv.data)*2)); uv.data.foreach_get('uv',a); h.update(a.tobytes())
        h.update(json.dumps([[(g.group,g.weight) for g in v.groups] for v in m.vertices],separators=(',',':')).encode())
        keys=[]
        if m.shape_keys:
            for k in m.shape_keys.key_blocks:
                a=array.array('f',[0.]*(len(k.data)*3)); k.data.foreach_get('co',a); h.update(a.tobytes())
                keys.append((k.name,k.value,k.mute,k.relative_key.name))
        result[o.name]={'hash':h.hexdigest(),'matrix':list(c for row in o.matrix_world for c in row),'groups':[g.name for g in o.vertex_groups],
                        'keys':keys,'parent':o.parent.name if o.parent else None,'modifiers':[(x.type,scalars(x),getattr(x,'object',None).name if getattr(x,'object',None) else None) for x in o.modifiers],
                        'vertices':len(m.vertices),'polygons':len(m.polygons),'hiddenRender':o.hide_render,
                        'materials':[m.name if m else None for m in m.materials]}
    return result

def materials():
    def value(i):
        x=getattr(i,'default_value',None)
        return list(x) if x is not None and hasattr(x,'__iter__') and not isinstance(x,str) else x
    result={}
    for m in bpy.data.materials:
        props=scalars(m)
        if m.name=='AFN6_Cornea': props.pop('thickness_mode',None)
        result[m.name]={'properties':props,'nodes':[(n.name,n.bl_idname,[(i.name,value(i)) for i in n.inputs if not(m.name=='AFN6_Cornea' and n.bl_idname=='ShaderNodeOutputMaterial' and i.name=='Thickness')]) for n in m.node_tree.nodes] if m.use_nodes else [],
                        'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links] if m.use_nodes else []}
    return result

def state():
    rig=bpy.data.objects['AFN_R0005_Rig']; s=bpy.context.scene
    return {'meshes':meshes(),'materialsExceptDeclaredThickness':materials(),'rig':{
        'bones':[(b.name,b.parent.name if b.parent else None,list(v for row in b.matrix_local for v in row),b.use_deform) for b in rig.data.bones],
        'poses':[(b.name,list(v for row in b.matrix_basis for v in row),b.rotation_mode) for b in rig.pose.bones],
        'matrix':list(v for row in rig.matrix_world for v in row)},
        'lights':{o.name:{'matrix':list(v for row in o.matrix_world for v in row),'data':scalars(o.data),'colour':list(o.data.color)} for o in bpy.data.objects if o.type=='LIGHT'},
        'colourManagement':scalars(s.view_settings),'world':[(n.name,[(i.name,str(getattr(i,'default_value',None))) for i in n.inputs]) for n in s.world.node_tree.nodes],
        'eevee':scalars(s.eevee),'raytracing':scalars(s.eevee.ray_tracing_options),
        'images':{im.name:{'size':list(im.size),'packed':bool(im.packed_file),'pixelsSha256':floats(im.pixels[:])} for im in bpy.data.images if im.source=='FILE'},
        'bodyMaterial':[(n.name,[(i.name,str(getattr(i,'default_value',None))) for i in n.inputs]) for n in bpy.data.materials['AFN_R0005_Clay'].node_tree.nodes]}

bpy.ops.wm.open_mainfile(filepath=str(BASE)); old=state()
bpy.ops.wm.open_mainfile(filepath=str(CAND)); new=state()
matches={k:old[k]==new[k] for k in old}
if not all(matches.values()):
    print('STATE_DIFF='+repr({k:(old[k],new[k]) for k in old if not matches[k]}))
assert all(matches.values()),matches
m=bpy.data.materials['AFN6_Cornea']; bsdf=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled'); out=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeOutputMaterial')
assert m.thickness_mode=='SLAB' and abs(out.inputs['Thickness'].default_value-.00055)<1e-9
assert abs(bsdf.inputs['IOR'].default_value-1.376)<1e-6 and bsdf.inputs['Transmission Weight'].default_value==1.
proof=R/'Evidence/character-female-next/r0008-evaluated-sockets/closed-solid-verification.json'
prior=json.loads(proof.read_text()); cert=next(x for x in prior['results'] if x['label']=='a-tight')
assert cert['fileSha256']==hashlib.sha256(BASE.read_bytes()).hexdigest()
result={'status':'PASS','savedFileOpenedWithoutAddon':True,'candidate':str(CAND),'candidateSha256':hashlib.sha256(CAND.read_bytes()).hexdigest(),
        'sourceSha256':cert['fileSha256'],'stateEquality':matches,'meshCount':len(new['meshes']),
        'collisionEvidenceInheritedFrom':str(proof),'collisionEvidenceSha256':hashlib.sha256(proof.read_bytes()).hexdigest(),
        'collisionScope':'Only the five r0008 sampled static poses: neutral, eye gaze +/-10deg and head turns +/-20deg. No blink, swept collision or animation guarantee.',
        'cornea':{'IOR':bsdf.inputs['IOR'].default_value,'transmission':bsdf.inputs['Transmission Weight'].default_value,'mode':m.thickness_mode,'thicknessM':out.inputs['Thickness'].default_value},
        'modelStatistics':{'bodyVertices':len(bpy.data.objects['AFN_R0008_Body'].data.vertices),'bodyQuads':len(bpy.data.objects['AFN_R0008_Body'].data.polygons),'rigBones':len(bpy.data.objects['AFN_R0005_Rig'].data.bones),'eyeTriangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN6_')),'fileBytes':CAND.stat().st_size},
        'externalLibraries':[l.filepath for l in bpy.data.libraries],'enginePerformance':'NOT_TESTED','overallCharacterScore':None}
assert not result['externalLibraries']
(E/'saved-optics-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('AFN_R0009_VERIFIED='+json.dumps(matches))
