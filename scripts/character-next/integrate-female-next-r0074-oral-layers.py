"""Non-destructive displayed oral layers from one stable editable deformation source."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
sp=importlib.util.spec_from_file_location('oral74',Path(__file__).with_name('build-female-next-r0074-oral-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
R=m.R;S=m.S;E=m.E;OUT=S/'aevrynd-female-next-r0074-a-layered-mouth-controls-study.blend'
NAMES={0:'AFN74_SKIN_AND_EXISTING_OCULAR_LINING',1:'AFN74_UPPER_TEETH',2:'AFN74_LOWER_TEETH',3:'AFN74_LOWER_GUM_REGION',4:'AFN74_TONGUE_REGION',5:'AFN74_UPPER_GUM_AND_ORAL_CAVITY'}
def main():
    tick=time.time();ref=json.loads((E/'a-build-summary.json').read_text());assert not OUT.exists() and m.sha(Path(ref['output']))==ref['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;s.frame_set(1);body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']
    islands=json.loads((E/'source-oral-uv-islands.json').read_text());assert len(islands)==35
    roles={};counts={};mapping=[]
    for i,row in enumerate(islands):
        if i==0:role=5
        elif i==1:role=3
        elif i==2:role=4
        else:
            assert row['faceCount']==108 and row['vertices']==125
            assert row['jawAffected'] in (0,125)
            role=1 if row['jawAffected']==0 else 2
        counts[role]=counts.get(role,0)+1
        for f in row['faces']:assert f not in roles;roles[f]=role
        mapping.append({'uvIsland':i,'role':role,'name':NAMES[role],'nativeFaceIDs':row['faces'],'nativeVertexIDs':row['nativeIDs'],'evidence':'Publisher UV chart, arch geometry, native opening correspondence. Gum/cavity labels inferred and explicitly combined, not source anatomy annotations.'})
    assert counts[1]==16 and counts[2]==16 and len(roles)==8774
    z=np.load(m.D/'Tongue_Up.npz',allow_pickle=False);assert set(z['idx'].tolist())<=set(islands[2]['nativeIDs'])
    nativefaces=np.array([v.value for v in body.data.attributes['AFN60_NativeFaceID'].data]);assert set(roles)<=set(nativefaces.tolist())
    values=np.array([roles.get(int(f),0) for f in nativefaces],dtype='i4');a=body.data.attributes.new('AFN74_OralRole','INT','FACE');a.data.foreach_set('value',values)
    collection=bpy.data.collections.new('AFN74_10_DISPLAY_LAYERS');s.collection.children.link(collection);parts=[]
    for role,name in NAMES.items():
        mesh=bpy.data.meshes.new(name+'_DISPLAY_INPUT');o=bpy.data.objects.new(name,mesh);collection.objects.link(o);o.matrix_world=body.matrix_world.copy()
        ng=bpy.data.node_groups.new(name+'_FROM_STABLE_MASTER','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=ng.nodes;links=ng.links
        info=nodes.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=body;info.inputs['As Instance'].default_value=False
        attr=nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='INT';attr.inputs['Name'].default_value='AFN74_OralRole'
        compare=nodes.new('FunctionNodeCompare');compare.data_type='INT';compare.operation='NOT_EQUAL';compare.inputs['B'].default_value=role;links.new(attr.outputs['Attribute'],compare.inputs['A'])
        delete=nodes.new('GeometryNodeDeleteGeometry');delete.domain='FACE';delete.mode='ALL';links.new(info.outputs['Geometry'],delete.inputs['Geometry']);links.new(compare.outputs[0],delete.inputs['Selection'])
        out=nodes.new('NodeGroupOutput');links.new(delete.outputs[0],out.inputs[0]);md=o.modifiers.new('AFN74_DISPLAY_LAYER_FROM_EDITABLE_MASTER','NODES');md.node_group=ng
        o['AFN74_role']=role;o['editing']='Display layer generated after original subdivision from the shared editable master. Edit native cage/keys/UV/masks on AFN60_BODY_ORAL_AND_OCULAR_LINING. Toggle this object independently. This is not an independent sculpt cage or runtime mesh.';parts.append(o)
    body.hide_render=True;body.hide_set(True);body['AFN74_editing']='Shared authoritative cage, expression, weights and UV. Unhide to edit, then hide again to avoid doubled display. All AFN74 display layers and existing hair root frames read this unchanged evaluated topology.'
    ctrl=bpy.data.objects['AFN74_ORAL_CONTROLS'];ctrl['layer_scope']='32 tooth charts:16 upper,16 lower; lower gum region; source tongue region; upper gum and oral cavity remain combined. Independent display toggles; shared editable deformation source, not yet independent cages.'
    s['AFN74_scope']='Layered actual complete woman, native neutral/open/return control. Stable original body remains the scalp-deformation reference. No fully separate gum/cavity cages, continuous contact, complete facial rig, hair dynamics or engine acceptance.'
    s.frame_set(1);bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0;m.m.k.b.camera('face');s.camera.data.lens=85
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.save('a-layer-build-summary.json',{'source':ref['output'],'sourceSha256':ref['outputSha256'],'output':str(OUT),'outputSha256':m.sha(OUT),'outputBytes':OUT.stat().st_size,'parts':NAMES,'sourceOralFaces':8774,'toothUVCharts':{'upper':16,'lower':16},'sharedMaster':body.name,'sharedMasterNativeTopologyUnchanged':True,'actualScalpBindingSourceUnchanged':True,'mapping':mapping,'tongueExpressionIDsContainedInTongueChart':True,'limitations':['Display layers are independently toggled, but original cage editing remains shared.','Upper gum and oral cavity are combined, not fully independent anatomy.','Region roles inferred from real geometry/UV/expression, not publisher-provided labels.','No new contact, natural dynamics or engine acceptance.'],'secondsBeforePilot':time.time()-tick})
    s.frame_set(13);bpy.context.view_layer.update();m.save('a-layer-open-pilot-controls.json',[m.render('a-layer-open','face'),m.render('a-layer-open','body-face')])
    # Explicitly isolated anatomy evidence, never used as the whole-head result.
    hidden=[]
    keep={NAMES[i] for i in (1,2,3,4)}
    for o in s.objects:
        if o.type in ('MESH','CURVES') and not o.hide_render and o.name not in keep:hidden.append(o);o.hide_render=True
    c=s.camera;c.location=(0,-.34,1.445);target=Vector((0,-.105,1.390));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=24;s.render.filepath=str(E/'a-isolated-oral-structure-open.png');bpy.ops.render.render(write_still=True)
    print('R74_LAYERS_AND_REAL_COMPLETE_PILOTS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
