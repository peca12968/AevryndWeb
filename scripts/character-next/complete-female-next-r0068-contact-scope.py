"""Final bounded correction: constrain the whole generated output, not a branch.

Source graph wraps only one branch before Join Geometry. B fixed flyaways
but left the main failures identical. C applies the demonstrated stage after
the complete main output and uses live render-level body data, removing cache.
"""
from pathlib import Path
import bpy,numpy as np,time,sys,importlib.util
s=importlib.util.spec_from_file_location('guide68scope',Path(__file__).with_name('build-female-next-r0068-guide-surface.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OUT=m.S/'aevrynd-female-next-r0068-c-live-body-contact-study.blend'
def main():
    tick=time.time();m.shade.g.E=m.E
    if '--views' in sys.argv:
        r=m.read(m.E/'c-build-summary.json');assert m.m.sha(OUT)==r['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));m.shade.settings();m.m.save('c-full-view-controls.json',m.shade.render('c-guide',('face','body-face','oblique','profile','back','alternate-oblique')));return
    ref=m.read(m.E/'b-build-summary.json');src=Path(ref['output']);assert m.m.sha(src)==ref['outputSha256'] and not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(src));body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];collider=bpy.data.objects['AFN68_RENDER_BODY_CONTACT_REFERENCE'];changes=[]
    for md in body.modifiers:
        if md.type=='SUBSURF':changes.append({'bodyViewportLevelBefore':md.levels,'after':md.render_levels,'renderLevelUnchanged':md.render_levels});md.levels=md.render_levels
    for group in bpy.data.node_groups:
        for n in group.nodes:
            for i in n.inputs:
                if i.type=='OBJECT' and getattr(i,'default_value',None)==collider:i.default_value=body;changes.append({'group':group.name,'node':n.name,'socket':i.name,'target':body.name})
    core=bpy.data.node_groups['Shrinkwrap Hair Curves']
    for n in core.nodes:
        if n.bl_idname=='GeometryNodeObjectInfo':n.transform_space='RELATIVE'
    core.update_tag();data=collider.data;bpy.data.objects.remove(collider,do_unlink=True)
    if data.users==0:bpy.data.meshes.remove(data)
    main=bpy.data.objects['AFN68_EDITABLE_MAIN_GUIDES'];radius=ref['visibleComponents'][0]['localRadiusRangeM'][1];wrapper=bpy.data.node_groups.new('AFN68_COMPLETE_MAIN_CONTACT_STAGE','GeometryNodeTree');wrapper.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');wrapper.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');ni=wrapper.nodes.new('NodeGroupInput');no=wrapper.nodes.new('NodeGroupOutput');node=wrapper.nodes.new('GeometryNodeGroup');node.node_tree=core;next(i for i in node.inputs if i.name=='Surface' and i.type=='OBJECT').default_value=body;node.inputs['Offset Distance'].default_value=radius;node.inputs['Above Surface'].default_value=0.;node.inputs['Lock Roots'].default_value=True;wrapper.links.new(ni.outputs['Geometry'],node.inputs['Geometry']);wrapper.links.new(node.outputs['Geometry'],no.inputs['Geometry']);md=main.modifiers.new('AFN68_COMPLETE_OUTPUT_CONTACT','NODES');md.node_group=wrapper;main.update_tag();bpy.context.view_layer.update();raw={};components=[]
    for i,name in enumerate(('AFN68_EDITABLE_MAIN_GUIDES','AFN68_EDITABLE_FLYAWAY_GUIDES')):
        o=bpy.data.objects[name];o.update_tag();bpy.context.view_layer.update();d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;vis=bpy.data.objects['AFN68_MAIN_RENDER_CURVES' if i==0 else 'AFN68_FLYAWAY_RENDER_CURVES'];copy=d.copy();copy.name=vis.data.name+'C';vis.data=copy;P=m.array3(copy.position_data,'vector');counts=np.array([c.points_length for c in copy.curves],dtype='i4');rr=np.empty(len(P),dtype='f4');copy.attributes['radius'].data.foreach_get('value',rr);assert np.isfinite(P).all() and np.isfinite(rr).all() and (rr>=0).all();raw[str(i)+'positions']=P;raw[str(i)+'counts']=counts;raw[str(i)+'radii']=rr;components.append({'object':vis.name,'curves':len(counts),'points':len(P),'localRadiusRangeM':[float(rr.min()),float(rr.max())]})
    raw['matrix']=np.array(main.matrix_world);np.savez_compressed(m.E/'c-render-curve-data.npz',**raw);m.shade.settings();m.k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN68_status']='COMPLETE_MAIN_CONTACT_STAGE_PENDING_INDEPENDENT_TEST';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.m.save('c-build-summary.json',{'source':str(src),'sourceSha256':ref['outputSha256'],'baselineSource':str(m.SRC),'baselineSha256':m.SOURCE_SHA,'publisherSourceSha256':m.m.SHA,'sourceCredit':ref['sourceCredit'],'output':str(OUT),'outputSha256':m.m.sha(OUT),'visibleComponents':components,'reason':'Source wrap stage affected one pre-join branch; B main witnesses stayed identical while its new complete flyaway stage removed strong flyaway witnesses. Apply that same full-output scope to main, not more value tuning.','changes':changes,'sourceObjectInfoSpace':'RELATIVE for live body object in the active guide space','duplicateStaticBodyRenderCacheRemoved':True,'newHairPhysicsOrFullContactAccepted':False,'sourceRights':ref['sourceRights'],'secondsBeforePreview':time.time()-tick});m.m.save('c-preview-control.json',m.preview('c-guide'));print('R68_COMPLETE_OUTPUT_SCOPE',components,OUT.stat().st_size,time.time()-tick,flush=True)
if __name__=='__main__':main()
