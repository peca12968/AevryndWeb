"""Verify original character state is unchanged in the failed hair research asset."""
import bpy,json,hashlib,array,importlib.util
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0012-layered-hair';S=R/'engine/assets/characters/female-next/source'
spec=importlib.util.spec_from_file_location('prior',Path(__file__).with_name('verify-female-next-r0010-eye-rim.py'));prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def state():
    meshes={}
    for o in bpy.data.objects:
        if o.type!='MESH' or o.name.startswith('AFN12_'):continue
        h=hashlib.sha256();m=o.data
        for uv in m.uv_layers:
            a=array.array('f',[0.]*(len(uv.data)*2));uv.data.foreach_get('uv',a);h.update(a.tobytes())
        w=[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices];h.update(json.dumps(w,separators=(',',':')).encode())
        meshes[o.name]={'geometry':prior.geom(o),'uvWeights':h.hexdigest(),'parent':o.parent.name if o.parent else None,'matrix':list(v for row in o.matrix_world for v in row),'materials':[x.name for x in m.materials]}
    def value(i):
        x=getattr(i,'default_value',None);return list(x) if x is not None and hasattr(x,'__iter__') and not isinstance(x,str) else x
    materials={m.name:{'nodes':[(n.name,n.bl_idname,[(i.name,value(i)) for i in n.inputs]) for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]} for m in bpy.data.materials if m.use_nodes and not m.name.startswith('AFN12_')}
    rig=bpy.data.objects['AFN_R0005_Rig'];s=bpy.context.scene
    return {'originalMeshes':meshes,'originalMaterials':materials,'bones':[(b.name,list(v for row in b.matrix_local for v in row)) for b in rig.data.bones],'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy,o.data.size,list(o.data.color)) for o in bpy.data.objects if o.type=='LIGHT'],'view':(s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma),'nodeGroups':sorted(n.name for n in bpy.data.node_groups)}
source=S/'aevrynd-female-next-r0011-b-ridge-skin-brows-study.blend';candidate=S/'aevrynd-female-next-r0012-c-corrected-hair-study.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));old=state();bpy.ops.wm.open_mainfile(filepath=str(candidate));now=state();checks={k:old[k]==now[k] for k in old};assert all(checks.values()),checks
libs=[l.filepath for l in bpy.data.libraries];assert not libs
images=[{'name':i.name,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images if i.source=='FILE'];assert all(i['packed'] for i in images)
result={'candidateSha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'reopenedWithoutAddon':True,'originalStateEquality':checks,'packedImages':images,'externalLibraries':libs,'sourceIntegrityStatus':'PASS','hairAcceptanceStatus':'FAIL_OR_UNRESOLVED','scope':'This verifies source preservation only, not hair collision or visual acceptance.'}
(E/'saved-source-integrity.json').write_text(json.dumps(result,indent=2)+'\n');print('AFN_R0012_SOURCE_INTEGRITY='+json.dumps(checks))
