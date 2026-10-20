"""One reference-grounded correction, no parameter or collision-margin sweep.

Author text says Above Surface0 affects below-surface points. Restore that
original setting, and apply the same stage to the omitted flyaway layer.
"""
from pathlib import Path
import bpy,numpy as np,time,sys,importlib.util
s=importlib.util.spec_from_file_location('guide68semantics',Path(__file__).with_name('build-female-next-r0068-guide-surface.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
OUT=m.S/'aevrynd-female-next-r0068-b-surface-semantics-study.blend'
def main():
    tick=time.time();m.shade.g.E=m.E
    if '--views' in sys.argv:
        ref=m.read(m.E/'b-build-summary.json');assert m.m.sha(OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));m.shade.settings();m.m.save('b-full-view-controls.json',m.shade.render('b-guide',('face','body-face','oblique','profile','back','alternate-oblique')));return
    a=m.read(m.E/'a-build-summary.json');assert m.m.sha(m.OUT)==a['outputSha256'] and not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(m.OUT));collider=bpy.data.objects['AFN68_RENDER_BODY_CONTACT_REFERENCE'];main=bpy.data.objects['AFN68_EDITABLE_MAIN_GUIDES'];fly=bpy.data.objects['AFN68_EDITABLE_FLYAWAY_GUIDES'];changes=[]
    for md in main.modifiers:
        if md.type=='NODES' and md.node_group:
            for n in md.node_group.nodes:
                if n.bl_idname=='GeometryNodeGroup' and n.node_tree and n.node_tree.name.startswith('Shrinkwrap Hair Curves'):
                    before=n.inputs['Above Surface'].default_value;n.inputs['Above Surface'].default_value=0.;md.node_group.update_tag();changes.append({'node':n.name,'input':'Above Surface','before':before,'after':0.,'basis':'Restore original author value per supplied Shrinkwrap Hair Curves text; keep actual radius-derived Offset Distance unchanged.'})
    wrapper=bpy.data.node_groups.new('AFN68_FLYAWAY_SOURCE_CONTACT_STAGE','GeometryNodeTree');wrapper.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');wrapper.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');ni=wrapper.nodes.new('NodeGroupInput');no=wrapper.nodes.new('NodeGroupOutput');node=wrapper.nodes.new('GeometryNodeGroup');node.node_tree=bpy.data.node_groups['Shrinkwrap Hair Curves'];next(i for i in node.inputs if i.name=='Surface' and i.type=='OBJECT').default_value=collider;radius=a['visibleComponents'][1]['localRadiusRangeM'][1];node.inputs['Offset Distance'].default_value=radius;node.inputs['Above Surface'].default_value=0.;node.inputs['Lock Roots'].default_value=True;wrapper.links.new(ni.outputs['Geometry'],node.inputs['Geometry']);wrapper.links.new(node.outputs['Geometry'],no.inputs['Geometry']);md=fly.modifiers.new('AFN68_SOURCE_CONTACT_STAGE','NODES');md.node_group=wrapper;main.update_tag();fly.update_tag();bpy.context.view_layer.update();components=[];raw={}
    for i,name in enumerate(('AFN68_EDITABLE_MAIN_GUIDES','AFN68_EDITABLE_FLYAWAY_GUIDES')):
        guide=bpy.data.objects[name];d=guide.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;visible=bpy.data.objects['AFN68_MAIN_RENDER_CURVES' if i==0 else 'AFN68_FLYAWAY_RENDER_CURVES'];copy=d.copy();copy.name=visible.data.name+'B';visible.data=copy;P=m.array3(copy.position_data,'vector');counts=np.array([c.points_length for c in copy.curves],dtype='i4');rr=np.empty(len(P),dtype='f4');copy.attributes['radius'].data.foreach_get('value',rr);assert np.isfinite(P).all() and np.isfinite(rr).all() and (rr>=0).all();raw[str(i)+'positions']=P;raw[str(i)+'counts']=counts;raw[str(i)+'radii']=rr;components.append({'object':visible.name,'curves':len(counts),'points':len(P),'curvePointCounts':sorted(set(counts.tolist())),'localRadiusRangeM':[float(rr.min()),float(rr.max())]})
    raw['matrix']=np.array(main.matrix_world);np.savez_compressed(m.E/'b-render-curve-data.npz',**raw);m.shade.settings();m.k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN68_status']='RESTORED_SOURCE_SEMANTICS_PENDING_INDEPENDENT_CONTACT';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.m.save('b-build-summary.json',{'source':str(m.OUT),'sourceSha256':a['outputSha256'],'baselineSource':str(m.SRC),'baselineSha256':m.SOURCE_SHA,'publisherSourceSha256':m.m.SHA,'sourceCredit':a['sourceCredit'],'output':str(OUT),'outputSha256':m.m.sha(OUT),'visibleComponents':components,'changes':changes,'flyawayContactStageAdded':True,'existingRadiusProfileDensityAndOriginalBodyUnchanged':True,'changedOriginalAboveSurfaceRestoredNotSwept':True,'contactOrEngineAccepted':False,'sourceRights':a['sourceRights'],'secondsBeforePreview':time.time()-tick});m.m.save('b-preview-control.json',m.preview('b-guide'));print('R68_SEMANTICS_B_PREVIEW',components,time.time()-tick,flush=True)
if __name__=='__main__':main()
