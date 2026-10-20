"""Bounded independent coordinate/interface check after an actual failure."""
from pathlib import Path
import bpy,numpy as np,importlib.util
s=importlib.util.spec_from_file_location('guide68interface',Path(__file__).with_name('build-female-next-r0068-guide-surface.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
    ref=m.read(m.E/'a-build-summary.json');assert m.m.sha(m.OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(m.OUT));group=bpy.data.node_groups['Shrinkwrap Hair Curves'];nodes=[]
    for n in group.nodes:
        row={'name':n.name,'type':n.bl_idname,'inputs':[]}
        for key in ('operation','transform_space','data_type','mode','input_type'):
            if hasattr(n,key):row[key]=getattr(n,key)
        for i in n.inputs:
            v=None
            if hasattr(i,'default_value'):
                v=i.default_value
                if hasattr(v,'name'):v=v.name
                elif not isinstance(v,(int,float,str,bool)) and v is not None:v=list(v)
            row['inputs'].append({'name':i.name,'identifier':i.identifier,'type':i.type,'value':v,'linked':i.is_linked})
        nodes.append(row)
    target=bpy.data.objects['AFN68_RENDER_BODY_CONTACT_REFERENCE'];hair=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];samples=[]
    for space in ('ORIGINAL','RELATIVE'):
        for hidden in (True,False):
            target.hide_set(hidden);d=bpy.data.meshes.new('AFN68_INTERFACE_TEST');o=bpy.data.objects.new('AFN68_INTERFACE_TEST',d);bpy.context.scene.collection.objects.link(o);o.matrix_world=hair.matrix_world.copy();t=bpy.data.node_groups.new('AFN68_INTERFACE_TEST','GeometryNodeTree');t.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');out=t.nodes.new('NodeGroupOutput');info=t.nodes.new('GeometryNodeObjectInfo');info.transform_space=space;info.inputs['Object'].default_value=target;info.inputs['As Instance'].default_value=False;t.links.new(info.outputs['Geometry'],out.inputs['Geometry']);md=o.modifiers.new('Test','NODES');md.node_group=t;bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();P=m.array3(me.vertices,'co');samples.append({'space':space,'targetHideGet':hidden,'vertices':len(P),'localBounds':[P.min(0).tolist(),P.max(0).tolist()] if len(P) else None});ev.to_mesh_clear();bpy.data.objects.remove(o,do_unlink=True)
    m.m.save('collider-interface-diagnosis.json',{'sourceSha256':ref['outputSha256'],'sourceGroupNodes':nodes,'sourceGroupLinks':[(l.from_node.name,l.from_socket.name,l.from_socket.type,l.to_node.name,l.to_socket.name,l.to_socket.type) for l in group.links],'objectInfoCoordinates':samples,'expectedColliderLocalBounds':[np.array([v.co[:] for v in target.data.vertices]).min(0).tolist(),np.array([v.co[:] for v in target.data.vertices]).max(0).tolist()],'modelNotSavedOrOverwritten':True});print('R68_COLLIDER_INTERFACE',samples,flush=True)
if __name__=='__main__':main()
