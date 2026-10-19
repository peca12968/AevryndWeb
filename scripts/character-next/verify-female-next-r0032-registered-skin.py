"""Reopen material study, prove unchanged evaluated geometry and packed maps."""
import bpy,importlib.util,json,hashlib,sys,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('skin32',Path(__file__).with_name('build-female-next-r0032-registered-skin.py'));k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
b=k.b;E=k.E
def save(n,x):k.save(n,x)
def read(n):return json.loads((E/n).read_text(encoding='utf8'))
def evaluated_signature(o):
    v,t=b.evaluated(o,True);h=hashlib.sha256();h.update(v.tobytes());h.update(t.tobytes());return {'vertices':len(v),'triangles':len(t),'worldGeometrySha256':h.hexdigest()}
def material_signature(mat):
    rows=[]
    for n in mat.node_tree.nodes:
        values={}
        for socket in n.inputs:
            if hasattr(socket,'default_value'):
                v=socket.default_value
                if isinstance(v,(str,int,float,bool)):values[socket.name]=v
                elif hasattr(v,'__iter__'):values[socket.name]=list(v)
        rows.append({'name':n.name,'type':n.bl_idname,'inputs':values,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'imagePackedSha256':hashlib.sha256(n.image.packed_file.data).hexdigest() if n.type=='TEX_IMAGE' and n.image and n.image.packed_file else None})
    return {'nodes':rows,'links':[(x.from_node.name,x.from_socket.name,x.to_node.name,x.to_socket.name) for x in mat.node_tree.links]}
def stage_lights():return [(o.name,list(o.location),list(o.rotation_euler),list(o.scale),o.data.energy) for o in bpy.context.scene.objects if o.type=='LIGHT']
def main():
    start=time.time();report=read('build-verification.json');path=Path(report['output']);assert b.sha(path)==report['outputSha256'];assert b.sha(k.SRC)==report['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(k.SRC));visible=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render];original_eval={n:evaluated_signature(bpy.data.objects[n]) for n in visible};optical_materials={m.name:material_signature(m) for n in visible if n!=b.BODY for m in bpy.data.objects[n].data.materials if m};cfg=b.config(bpy.context.scene);lights=stage_lights()
    baseline_body,baseline_tri=b.evaluated(bpy.data.objects[b.BODY],True)
    bpy.ops.wm.open_mainfile(filepath=str(path));actual_state=k.mesh_state();controls={}
    for n,expected in report['originalMeshState'].items():
        actual=actual_state[n];good=actual['geometrySha256']==expected['geometrySha256'] and actual['parent']==expected['parent'] and actual['basis']==expected['basis'] and actual['parentInverse']==expected['parentInverse'] and all(u in actual['UV'] for u in expected['UV']);assert good,n;controls[n]=True
    actual_eval={n:evaluated_signature(bpy.data.objects[n]) for n in visible}
    current_body,current_tri=b.evaluated(bpy.data.objects[b.BODY],True)
    save('evaluated-geometry-inspection.json',{'before':original_eval,'after':actual_eval,'bodyTriangulationExact':bool(np.array_equal(baseline_tri,current_tri)),'bodyVertexOrderMaximumDifferenceM':float(np.linalg.norm(current_body-baseline_body,axis=1).max()) if current_body.shape==baseline_body.shape else None,'bodyChangedVertexCount':int(np.any(current_body!=baseline_body,axis=1).sum()) if current_body.shape==baseline_body.shape else None})
    assert actual_eval==original_eval
    actual_materials={name:material_signature(bpy.data.materials[name]) for name in optical_materials};assert actual_materials==optical_materials;assert b.config(bpy.context.scene)==cfg and stage_lights()==lights;assert not bpy.data.libraries and not bpy.data.texts
    body=bpy.data.objects[b.BODY];m=body.data;loops=np.empty(len(m.loops),dtype='i4');m.loops.foreach_get('vertex_index',loops)
    if report.get('newMappingAttribute'):
        vector=np.empty(len(m.vertices)*3,dtype='f4');m.attributes[report['newMappingAttribute']].data.foreach_get('vector',vector);uv=vector.reshape(-1,3)[:,:2][loops]
    else:
        uv=np.empty(len(m.loops)*2,dtype='f4');m.uv_layers[report['newUVLayer']].data.foreach_get('uv',uv);uv=uv.reshape(-1,2)
    weight=np.empty(len(m.vertices),dtype='f4');m.attributes['AFN32_PigmentWeight'].data.foreach_get('value',weight);weightloops=weight[loops];undefined_active=int(np.sum((np.linalg.norm(uv,axis=1)<1e-8)&(weightloops>1e-6)));assert undefined_active==0
    fields={}
    for name in ('AFN32_PigmentWeight','AFN32_Roughness'):
        data=np.empty(len(m.vertices),dtype='f4');m.attributes[name].data.foreach_get('value',data);assert np.isfinite(data).all();fields[name]={'minimum':float(data.min()),'maximum':float(data.max()),'sha256':hashlib.sha256(data.tobytes()).hexdigest()}
    images=[]
    for mat in m.materials:
        for n in mat.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image:
                im=n.image;assert im.packed_file;images.append({'name':im.name,'packed':True,'packedSha256':hashlib.sha256(im.packed_file.data).hexdigest(),'colorSpace':im.colorspace_settings.name})
    assert images[0]['packedSha256']==report['texture']['sha256']
    shader=m.materials[0].node_tree.nodes.get('Principled BSDF');output=m.materials[0].node_tree.nodes.get('Material Output');assert not output.inputs['Displacement'].is_linked
    shader_state={'subsurfaceWeight':shader.inputs['Subsurface Weight'].default_value,'subsurfaceScale':shader.inputs['Subsurface Scale'].default_value,'Ior':shader.inputs['IOR'].default_value,'noDisplacementInput':True};render=None
    if k.CHART:
        b.camera('face');s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4;s.render.filepath=str(E/'reopened-face.png');bpy.ops.render.render(write_still=True);render={'path':s.render.filepath,'scope':'Actual reopened standalone source rendered with its packed image and saved shader fields.'}
    result={'source':str(path),'sourceSha256':b.sha(path),'savedFileOpened':True,'nativeSourceUVPreserved':True,'originalMeshControlsExact':controls,'allDisplayedEvaluatedGeometryExact':actual_eval,'originalEightOpticalMaterialsExact':True,'stageAndLightingExact':True,'externalLibraries':0,'activeSkinImages':images,'nativeFields':fields,'shader':shader_state,'additionalUVMappedActiveLoops':int((weightloops>1e-6).sum()),'undefinedAdditionalUVAtActiveLoops':undefined_active,'reopenedRender':render,'inheritedContact':{'path':str(k.R/'Evidence/character-female-next/r0030-eye-optics/b/saved-optical-verification.json'),'sourceSha256':report['sourceSha256'],'basis':'All actual displayed body/optical evaluated vertex+triangle SHA signatures match exact source. No new geometry or displacement, so the existing neutral scope remains valid.','scope':'No new gaze/blink/continuous/hair/cloth/runtime proof.'},'status':'PASS_REOPENED_MATERIAL_DATA_AND_EXACT_SOURCE_GEOMETRY','seconds':time.time()-start,'limits':report['limits']};save('saved-material-verification.json',result);print('R0032_VERIFY_DONE',json.dumps({'status':result['status'],'visibleMeshes':len(actual_eval),'bodyVertices':actual_eval[b.BODY]['vertices'],'packedSkinImages':images,'seconds':result['seconds']}),flush=True)
if __name__=='__main__':main()
