"""Independent saved-data, complete neutral return and actual displayed dental checks."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0074-oral-controls'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def arr(data,prop,n,width=1,dtype='f4'):
    x=np.empty((n,width),dtype);data.foreach_get(prop,x.ravel());return x if width>1 else x[:,0]
def native(o):
    d=o.data;h=hashlib.sha256();h.update(arr(d.vertices,'co',len(d.vertices),3).tobytes());h.update(arr(d.loops,'vertex_index',len(d.loops),dtype='i4').tobytes());h.update(arr(d.polygons,'material_index',len(d.polygons),dtype='i4').tobytes())
    for uv in d.uv_layers:h.update(uv.name.encode());h.update(arr(uv.data,'uv',len(uv.data),2).tobytes())
    for k in d.shape_keys.key_blocks:
        if k.name.startswith('AFN74_'):continue
        h.update(k.name.encode());h.update(arr(k.data,'co',len(k.data),3).tobytes());h.update(str(k.value).encode())
    for v in d.vertices:
        for g in v.groups:h.update(np.array([g.group,g.weight],'f8').tobytes())
    return h.hexdigest()
def geom(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=arr(d.vertices,'co',len(d.vertices),3).astype('f8');a=np.array(o.matrix_world);return d,p@a[:3,:3].T+a[:3,3]
def hair(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=arr(d.position_data,'vector',len(d.position_data),3).astype('f8');a=np.array(o.matrix_world);return p@a[:3,:3].T+a[:3,3]
def main():
    tick=time.time();src=S/'aevrynd-female-next-r0069-a-complete-controls-study.blend';assert sha(src)=='f358d3c5a4d00ee6ad94d324612b33bdcf5aa4dde0bb19382d72bc7afabbb667'
    bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(1);names=[o.name for o in bpy.data.objects if o.type=='MESH' and o.data.attributes.get('AFN60_NativeVertexID')];assert len(names)==5
    native_old={n:native(bpy.data.objects[n]) for n in names};neutral={n:geom(bpy.data.objects[n])[1].copy() for n in names};hairnames=['AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES'];neutralhair={n:hair(bpy.data.objects[n]).copy() for n in hairnames}
    oldlights={o.name:(list(o.matrix_world),o.data.energy,tuple(o.data.color)) for o in bpy.data.objects if o.type=='LIGHT'};oldlights={n:str(v) for n,v in oldlights.items()}
    ref=json.loads((E/'c-build-summary.json').read_text());p=Path(ref['output']);assert sha(p)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(p));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
    assert {n:native(bpy.data.objects[n]) for n in names}==native_old
    assert oldlights=={o.name:str((list(o.matrix_world),o.data.energy,tuple(o.data.color))) for o in bpy.data.objects if o.type=='LIGHT'}
    assert not bpy.data.libraries;images=[]
    for im in bpy.data.images:
        if im.packed_file or im.source!='FILE':continue
        image=Path(bpy.path.abspath(im.filepath));assert image.is_file();images.append({'relative':im.filepath,'sha256':sha(image)})
    body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];assert body.hide_render and body.hide_get();rig=bpy.data.objects['AFN69_BODY_CONTROLS'];assert len(rig.data.bones)==52 and rig.animation_data.action is None
    ctrl=bpy.data.objects['AFN74_ORAL_CONTROLS'];assert bpy.data.actions.get('AFN69_CONTROLLED_HEAD_TURN_AND_ARM_RAISE')
    for n in hairnames:
        ng=bpy.data.objects[n].modifiers['AFN69_LIVE_RENDER_SCALP_FRAME'].node_group;assert any(x.bl_idname=='GeometryNodeObjectInfo' and x.inputs['Object'].default_value==body for x in ng.nodes)
    d,lower0=geom(bpy.data.objects['AFN74_LOWER_TEETH_RIGID']);edges=arr(d.edges,'vertices',len(d.edges),2,'i4');length0=np.linalg.norm(lower0[edges[:,1]]-lower0[edges[:,0]],axis=1);assert length0.min()>1e-9
    upper0=geom(bpy.data.objects['AFN74_UPPER_TEETH_RIGID'])[1].copy();rows=[]
    for frame,value in ((1,0),(7,.5),(13,1),(25,1),(31,.5),(37,0)):
        s.frame_set(frame);bpy.context.view_layer.update();assert abs(ctrl['jaw_open']-value)<1e-6
        for pb in rig.pose.bones:assert np.max(np.abs(np.array(pb.matrix_basis)-np.eye(4)))<1e-6
        master,world=geom(body);assert np.isfinite(world).all();lower=geom(bpy.data.objects['AFN74_LOWER_TEETH_RIGID'])[1];upper=geom(bpy.data.objects['AFN74_UPPER_TEETH_RIGID'])[1]
        strain=float(np.max(np.abs(np.linalg.norm(lower[edges[:,1]]-lower[edges[:,0]],axis=1)/length0-1)));assert strain<1e-5,strain
        upper_error=float(np.linalg.norm(upper-upper0,axis=1).max());assert upper_error<1e-6,upper_error
        row={'frame':frame,'jawOpen':float(ctrl['jaw_open']),'actualLowerDentalMaximumRelativeEdgeLengthChange':strain,'actualUpperTeethMaximumWorldDeltaM':upper_error,'lowerDentalMaximumWorldDeltaM':float(np.linalg.norm(lower-lower0,axis=1).max())}
        if frame in (1,13,37):
            role=arr(master.attributes['AFN74_OralRole'].data,'value',len(master.polygons),dtype='i4');cnt=arr(master.polygons,'loop_total',len(master.polygons),dtype='i4');loopv=arr(master.loops,'vertex_index',len(master.loops),dtype='i4');looprole=np.repeat(role,cnt);corners=world[loopv];uv=arr(master.uv_layers['VitruvianUV.UDIM'].data,'uv',len(master.loops),2);parts={}
            for o in bpy.data.collections['AFN74_10_DISPLAY_LAYERS'].objects:
                if o.hide_render or 'AFN74_role' not in o:continue
                roleid=int(o['AFN74_role']);part,pw=geom(o);pv=arr(part.loops,'vertex_index',len(part.loops),dtype='i4');mask=looprole==roleid;expected=corners[mask];actual=pw[pv];assert actual.shape==expected.shape,(o.name,actual.shape,expected.shape)
                error=float(np.linalg.norm(actual-expected,axis=1).max());assert error<1e-6,(o.name,error)
                puv=arr(part.uv_layers['VitruvianUV.UDIM'].data,'uv',len(part.loops),2);assert np.max(np.abs(puv-uv[mask]))<1e-6
                parts[o.name]={'faces':len(part.polygons),'loops':len(part.loops),'maximumMasterWorldErrorM':error,'UVMatchesExactMasterLoopOrder':True}
            row['nonRigidDisplayPartition']=parts
        if frame in (1,37):
            row['completeNeutralGeometryMaximumErrorsM']={n:float(np.linalg.norm(geom(bpy.data.objects[n])[1]-neutral[n],axis=1).max()) for n in names};assert max(row['completeNeutralGeometryMaximumErrorsM'].values())<1e-6
            row['hairReturnMaximumErrorsM']={n:float(np.linalg.norm(hair(bpy.data.objects[n])-neutralhair[n],axis=1).max()) for n in hairnames};assert max(row['hairReturnMaximumErrorsM'].values())<1e-6
        rows.append(row);print('R74_VERIFY_FRAME',frame,row['actualLowerDentalMaximumRelativeEdgeLengthChange'],flush=True)
    result={'status':'PASS_SAVED_COMPLETE_NEUTRAL_RETURN_LAYER_PARTITION_AND_RIGID_DENTAL_OPERATION_SCOPE','source':str(p),'sha256':sha(p),'nativeFiveCagesOldKeysUVMaterialsWeightsExact':True,'original52BoneFKActionRetainedDetachedForMouthDemonstration':True,'stableHairScalpReferencePreserved':True,'externalTextures':images,'frames':rows,'anatomyLimit':'Upper gum/cavity combined; generated soft display layers share an editable cage. Both actual dental arch meshes independently editable.','noCompleteAppearanceContactNaturalDynamicsOrRuntimeAcceptance':True,'seconds':time.time()-tick}
    (E/'c-independent-readback.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('R74_SAVED_OPERATION_VERIFIED',time.time()-tick,flush=True)
if __name__=='__main__':main()
