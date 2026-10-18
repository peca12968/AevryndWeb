"""Fit CC0 oral graphical data to retained native helpers; bounded mouth pilot.

No MPFB program code or runtime is imported. MHCLO is read as graphical data
by our own parser. Dental rows use rigid controls rather than scaled morphs.
"""
import bpy, gzip, hashlib, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
from mathutils import Matrix

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import oral_proxy_data as proxy
def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value
native = module('native24', 'prepare-female-next-r0019-native-blink.py')
solid = module('solid24', 'verify-female-next-r0010-eye-rim.py')
route = module('route24', 'build-female-next-r0013-envelope-hair.py')
R = Path(r'D:\Download\Aevrynd')
S = R / 'engine/assets/characters/female-next/source'
E = R / 'Evidence/character-female-next/r0024-oral-layers'
HINGE = '--hinge' in sys.argv
LABEL = 'b' if HINGE else 'a'
DST = S / f'aevrynd-female-next-r0024-{LABEL}-oral-study.blend'
OPEN = .2
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name, data): (E/name).write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
def positions(o): return native.positions(o.data).astype(np.float64)
def evaluate(o): return np.array(solid.data(o)[0], np.float64)

def material(name, texture, roughness):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Roughness'].default_value = roughness
    p.inputs['IOR'].default_value = 1.45
    tex = m.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(texture), check_existing=True); tex.image.pack()
    m.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    m['aevrynd_license'] = 'CC0 texture; own Principled approximation, not original Phong/litsphere shader'
    return m

def mesh(name, P, faces, uvs, face_uv, selected, mat, rig):
    selected = sorted(selected); ids = sorted({v for i in selected for v in faces[i]})
    reindex = {v:i for i,v in enumerate(ids)}
    m = bpy.data.meshes.new(name)
    m.from_pydata(P[ids].tolist(), [], [[reindex[v] for v in faces[i]] for i in selected]); m.update()
    uv = m.uv_layers.new(name='OralUV')
    for poly, i in zip(m.polygons, selected):
        for li, ui in zip(poly.loop_indices, face_uv[i]):
            assert ui >= 0; uv.data[li].uv = uvs[ui]
        poly.use_smooth = True
    o = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat); route.parent_head(o, rig)
    o['aevrynd_source'] = 'MakeHuman Community CC0 system assets September 2020'
    o['aevrynd_original_vertex_indices'] = ids
    o['aevrynd_layer'] = {'AFN24_UpperTeeth':'TEETH_UPPER','AFN24_LowerTeeth':'TEETH_LOWER','AFN24_ContinuousGingivalLining':'ORAL_GINGIVAL_LINING','AFN24_Tongue':'TONGUE'}[name]
    o['aevrynd_status'] = 'RESEARCH_CONTACT_AND_VISUAL_ACCEPTANCE_REQUIRED'
    return o, np.array(ids, np.int32)

def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0)
    u,s,vt = np.linalg.svd((A-ca).T@(B-cb)); rot = vt.T@u.T
    if np.linalg.det(rot)<0: vt[-1] *= -1; rot = vt.T@u.T
    t = cb-rot@ca; err = np.linalg.norm(A@rot.T+t-B, axis=1)
    return rot,t,{'maxM':float(err.max()),'rmsM':float(np.sqrt(np.mean(err**2)))}

def add_linear_key(o, Q):
    o.shape_key_add(name='Basis'); key = o.shape_key_add(name='AFN24_MouthOpen')
    key.data.foreach_set('co', Q.astype(np.float32).ravel()); key.slider_max = OPEN
    return key

def main():
    started = time.time(); E.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((S.parent/'female-next.asset.json').read_text(encoding='utf8'))
    src = S.parent/manifest['workingReviewSource']; assert sha(src)==manifest['workingReviewSha256']
    save(LABEL+'-iteration-contract.json', {'previousGoalTurnClassification':'progress: v6 prompt and execution entry points saved and verified on GitHub; no model gain claimed.', 'stage':'B_COMPLETE_HEAD_IN_PROGRESS', 'source':str(src), 'sourceSha256':sha(src), 'primaryDefect':'Working head has no separate teeth, gums or tongue and cannot demonstrate a structurally complete open mouth.', 'hypothesis':'Official CC0 proxy bindings against the retained full native helpers place real oral layers without arbitrary visual scale/translation; rigid dental rows plus a small native open field expose fit problems before expanding motion.', 'alternativeReason':'A exact native-helper rigid transfer failed lower-row 0.5mm calibration gate. B uses a separate fixed-axis hinge approximation derived from those landmarks, validated against actual oral/body surfaces instead of claiming exact target reconstruction.' if HINGE else None, 'expectedVisibleChange':'Actual teeth/tongue/gingival depth in a small mouth opening, preserving the retained neutral lip rest and unrelated head/hair/skin/light.', 'rejectIf':['Oral/body or oral/other geometry intersects outside documented anatomical joins.', 'Dental fit or jaw transform is implausible or depends on ad hoc shrinking.', 'The native open field breaks the corrected lip rest or unrelated attachments.', 'Whole-head appearance regresses.'], 'budget':{'candidatesMaximum':3,'candidate':LABEL,'threads':4,'initialOpenWeights':[0,.2],'diagnosticMinutes':10,'roundCheckpointMinutes':45,'noChildHairGeneration':True}, 'scope':'Oral-layer candidate. No continuous motion, complete expressions, realistic hair or engine acceptance.'})
    bpy.ops.wm.open_mainfile(filepath=str(src)); rig=bpy.data.objects['AFN_R0005_Rig']
    solid.stage.set_pose(rig, 'neutral'); body=bpy.data.objects['AFN_R0008_Body']
    source_hashes={o.name:solid.geom(o) for o in bpy.data.objects if o.type=='MESH'}
    P=positions(body); raw=bpy.data.objects['AFN_R0005_EditableNativeCC0']
    temp=raw.copy(); temp.data=raw.data.copy(); bpy.context.scene.collection.objects.link(temp)
    temp.hide_viewport=False; temp.hide_set(False); temp.hide_render=True
    for modifier in temp.modifiers:
        if modifier.type=='MASK': modifier.show_viewport=modifier.show_render=False
    neutral, native_faces=native.evaluate(temp); assert len(neutral)==19158
    coarse=np.zeros((19158,3),np.float64)
    target_folder=S/'oral/cc0-mouth-open-targets'
    targets=[]
    for race,weight in (('african',.2),('asian',.5),('caucasian',.3)):
        path=target_folder/f'{race}-mouth-open.target.gz'
        rows=np.array([[float(x) for x in line.split()] for line in gzip.decompress(path.read_bytes()).decode('utf8').splitlines() if line and not line.startswith('#')])
        coarse[rows[:,0].astype(int)] += weight*proxy.to_blender(rows[:,1:4])
        targets.append({'path':str(path),'sha256':sha(path),'weight':weight,'license':'CC0 graphical target data'})
    basis=temp.data.shape_keys.key_blocks[0]; local=np.empty((len(basis.data),3),np.float32); basis.data.foreach_get('co',local.ravel())
    key=temp.shape_key_add(name='AFN24_TEMP_OPEN'); key.data.foreach_set('co',(local+coarse).astype(np.float32).ravel()); key.value=OPEN
    opened, same_faces=native.evaluate(temp); assert np.array_equal(native_faces,same_faces)
    key.value=0.; mesh_data=temp.data; bpy.data.objects.remove(temp,do_unlink=True); bpy.data.meshes.remove(mesh_data)
    high=np.load(S/'aevrynd-female-next-r0023-native-mouth-data.npz')
    assert np.array_equal(np.array([tuple(p.vertices) for p in body.data.polygons]),high['faces'])
    delta=high['delta_open'].astype(np.float64)
    bodykey=add_linear_key(body,P+delta)
    assets=S/'oral/makehuman-system-cc0'
    results={}; objects={}; cache={'bodyNeutral':P,'bodyDeltaOpen':delta,'nativeNeutral':neutral,'nativeOpened':opened}
    teeth_texture=assets/'teeth/teeth_base/teeth.png'
    teeth_mat=material('AFN24_CC0_DentalAndGingivalPBR',teeth_texture,.35)
    tongue_mat=material('AFN24_CC0_TonguePBR',assets/'tongue/tongue01/tongue01_diffuse.png',.42)
    controls=[]
    for kind,folder,stem,mat in (('teeth',assets/'teeth/teeth_base','teeth_base',teeth_mat),('tongue',assets/'tongue/tongue01','tongue01',tongue_mat)):
        V,uv,F,FUV=proxy.obj(folder/(stem+'.obj')); mapping=proxy.proxy(folder/(stem+'.mhclo'))
        assert len(V)==len(mapping['ids'])
        fitted,scales=proxy.fit(mapping,proxy.to_mh(neutral)); raw_open,raw_open_scales=proxy.fit(mapping,proxy.to_mh(opened))
        fitted_open,scales_open=proxy.fit(mapping,proxy.to_mh(opened),scale_factors=scales)
        Q=proxy.to_blender(fitted); Qopen=proxy.to_blender(fitted_open)
        groups=proxy.components(len(Q),F)
        info={'vertices':len(Q),'faces':len(F),'components':[len(g) for g in groups], 'neutralScaleFactors':scales.tolist(),'openScaleFactors':scales_open.tolist(),'rejectedDynamicScaleFactors':raw_open_scales.tolist(),'poseScalePolicy':'Body adaptation scales frozen at neutral; motion from anatomical helper references, dental rows strictly rigid.', 'neutralBoundsM':[Q.min(0).tolist(),Q.max(0).tolist()], 'maxFittedOpenMoveM':float(np.linalg.norm(Qopen-Q,axis=1).max()), 'proxySha256':sha(folder/(stem+'.mhclo')), 'objSha256':sha(folder/(stem+'.obj'))}
        if kind=='teeth':
            assert len(groups)==33 and len(groups[0])==1852 and all(len(g)==63 for g in groups[1:])
            centres=np.array([V[g].mean(0) for g in groups[1:]])
            design=np.column_stack((np.ones(32),centres[:,2],abs(centres[:,0])))
            coeff=np.linalg.lstsq(design,centres[:,1],rcond=None)[0]; residual=centres[:,1]-design@coeff
            upper=[g for g,r in zip(groups[1:],residual) if r>0]; lower=[g for g,r in zip(groups[1:],residual) if r<0]
            assert len(upper)==len(lower)==16 and abs(residual).min()>.005
            info['rowClassification']={'method':'Original asset tooth-centroid height residual from depth/lateral regression; no fixed horizontal slicing.', 'regression':coeff.tolist(),'residualsMH':residual.tolist(),'upperTeeth':16,'lowerTeeth':16}
            partitions=[('AFN24_UpperTeeth',sum(upper,[])),('AFN24_LowerTeeth',sum(lower,[])),('AFN24_ContinuousGingivalLining',groups[0])]
        else: partitions=[('AFN24_Tongue',list(range(len(Q))))]
        for name,ids in partitions:
            idset=set(ids); selected=[i for i,f in enumerate(F) if set(f).issubset(idset)]
            o,indices=mesh(name,Q,F,uv,FUV,selected,mat,rig); objects[name]=o
            if name.endswith('Teeth'):
                refs=np.unique(mapping['ids'][indices])
                rot,t,error=kabsch(neutral[refs],opened[refs]); angle=math.atan2(rot[2,1],rot[1,1])
                pivot=np.linalg.lstsq(np.eye(3)-rot,t,rcond=None)[0]
                axis_error=float(np.max(np.abs(rot-np.array(((1,0,0),(0,math.cos(angle),-math.sin(angle)),(0,math.sin(angle),math.cos(angle)))))))
                helper_rot,helper_t,helper_err=kabsch(neutral[refs],opened[refs])
                if not (E/(name+'-rigid-fit-diagnosis.json')).exists():
                    _,_,raw_err=kabsch(Q[indices],proxy.to_blender(raw_open)[indices])
                    save(name+'-rigid-fit-diagnosis.json',{'row':name,'proxyNeutralScaleFactors':scales.tolist(),'proxyOpenedScaleFactors':raw_open_scales.tolist(),'proxyRefitRigidityError':raw_err,'helperRigidFitError':helper_err,'helperMaximumMoveM':float(np.linalg.norm(opened[refs]-neutral[refs],axis=1).max()),'helperIds':refs.tolist(),'helperRotation':helper_rot.tolist(),'helperTranslationM':helper_t.tolist(),'status':'DYNAMIC_ADAPTATION_REJECTED_USE_STATIC_ADAPTATION_WITH_RIGID_HELPER_POSE'})
                # A measured rigid fit is retained only when close to the authored
                # small-pose data. This is not evidence of a calibrated TMJ joint.
                if not HINGE and (error['maxM']>=.0005 or axis_error>=.002):
                    save('a-rejection.json',{'status':'REJECT_EXACT_NATIVE_HELPER_RIGID_TRANSFER','row':name,'helperRigidResidualM':error,'maximumAllowedM':.0005,'reason':'Authored helper movement is nonrigid; do not deform dental crowns to reproduce it. No A asset completed.','nextArchitecture':'Independent fixed-axis rigid hinge, explicitly approximate, must pass actual oral/body checks before retention.'})
                    raise AssertionError((name,error,axis_error))
                assert axis_error<.002
                hinge_error=float(np.linalg.norm((np.eye(3)-rot)@pivot-t))
                if abs(angle)<1.e-6: pivot=np.zeros(3); angle=0.
                else: assert HINGE and hinge_error<1.e-6 and -.12<pivot[1]<.02 and 1.35<pivot[2]<1.48,(pivot,hinge_error)
                control=bpy.data.objects.new(name.replace('Teeth','RigidControl'),None); bpy.context.scene.collection.objects.link(control)
                route.parent_head(control,rig)
                # The polar closest rigid transform defines a pose control. A
                # quaternion slerp + translation preserves all tooth dimensions.
                o.parent=control; o.parent_type='OBJECT'; o.matrix_parent_inverse=Matrix.Identity(4); o.matrix_basis=Matrix.Identity(4)
                o.data.vertices.foreach_set('co',(Q[indices]-pivot).astype(np.float32).ravel()); control.location=pivot
                controls.append((control,angle))
                info[name]={'nativeHelperRigidApproximationError':error,'rotation':rot.tolist(),'translationM':t.tolist(),'angleDegrees':math.degrees(angle),'axisXApproximationError':axis_error,'derivedPivotM':pivot.tolist(),'hingeEquationResidualM':hinge_error,'control':control.name,'note':'Independent fixed-axis hinge approximation. A failed exact helper reconstruction is not a pass; actual contact and visual gates govern B.'}
            else:
                add_linear_key(o,Q[indices]+(Qopen[indices]-Q[indices])/OPEN)
            cache[name+'_neutral']=Q[indices]; cache[name+'_open']=Qopen[indices]
            info[name+'_topology']={'vertices':len(indices),'faces':len(selected)}
        results[kind]=info
    # Simple locally authored drivers are stored as Blender expressions; no
    # addon handler or embedded external program is required on reopening.
    # Keep the UI property control independent of the deform hierarchy. The
    # head-parented version made the body shape driver invalid in this file;
    # its removal is verified by actual evaluator errors and reopening.
    master=bpy.data.objects.new('AFN24_MouthControl',None); bpy.context.scene.collection.objects.link(master)
    master['open']=0.; master.id_properties_ui('open').update(min=0.,max=OPEN,description='CC0 native mouth-open weight, verified static endpoints only')
    bpy.context.view_layer.update()
    def driver(target,path,index=None,expression='w'):
        curve=target.driver_add(path) if index is None else target.driver_add(path,index)
        d=curve.driver; d.type='SCRIPTED'
        for old in list(d.variables): d.variables.remove(old)
        var=d.variables.new(); var.name='w'; var.type='SINGLE_PROP'; var.targets[0].id_type='OBJECT'; var.targets[0].id=master; var.targets[0].data_path='["open"]'; d.expression=expression
    driver(bodykey,'value')
    for o in objects.values():
        if o.data.shape_keys: driver(o.data.shape_keys.key_blocks['AFN24_MouthOpen'],'value')
    for control,angle in controls:
        control.rotation_mode='AXIS_ANGLE'; control.rotation_axis_angle=(0.,1.,0.,0.)
        driver(control,'rotation_axis_angle',0,repr(float(angle/OPEN))+'*w')
    bpy.context.view_layer.update()
    attachment_paths=[R/'Evidence/character-female-next/r0010-eye-rim/c-spaced-lashes-lash-bindings.json',S/'aevrynd-female-next-r0018-c-brow-bindings.json',S/'aevrynd-female-next-r0014-root-bindings.json']
    attachment_move={str(p):max(float(np.linalg.norm(delta[row['bodyVertices']]*OPEN,axis=1).max()) for row in json.loads(p.read_text(encoding='utf8'))) for p in attachment_paths}
    assert source_hashes=={n:solid.geom(bpy.data.objects[n]) for n in source_hashes}
    for w in (0.,OPEN):
        master['open']=w; master.update_tag(refresh={'OBJECT'}); bpy.context.scene.frame_set(bpy.context.scene.frame_current+1); bpy.context.view_layer.update()
        error=float(np.linalg.norm(evaluate(body)-(P+delta*w),axis=1).max())
        print('R0024_DRIVER_CONTROL',w,bodykey.value,error,flush=True)
        if error>=5.e-7:
            save('driver-diagnosis.json',{'weight':w,'masterValue':master['open'],'keyValue':bodykey.value,'autoexecFail':bpy.app.autoexec_fail,'drivers':[{'path':c.data_path,'valid':c.is_valid,'driverValid':c.driver.is_valid,'expression':c.driver.expression,'simple':c.driver.is_simple_expression,'variables':[{'name':v.name,'id':v.targets[0].id.name if v.targets[0].id else None,'path':v.targets[0].data_path} for v in c.driver.variables]} for c in body.data.shape_keys.animation_data.drivers]})
        assert error<5.e-7,{'weight':w,'evaluatedKey':bodykey.value,'errorM':error}
    master['open']=0.; master.update_tag(); bpy.context.view_layer.update()
    for collection_name, collection_objects in (('AFN24_ORAL_GEOMETRY',list(objects.values())),('AFN24_ORAL_CONTROLS',[master]+[o for o,angle in controls])):
        collection=bpy.data.collections.new(collection_name);bpy.context.scene.collection.children.link(collection)
        for o in collection_objects:
            for old in list(o.users_collection):old.objects.unlink(o)
            collection.objects.link(o)
            if o.type=='EMPTY':o['aevrynd_layer']='ORAL_CONTROL'
    for image in bpy.data.images:
        if image.source=='FILE' and not image.packed_file: image.pack()
    bpy.context.scene['aevrynd_revision']='female-next-r0024-'+LABEL
    bpy.context.scene['aevrynd_release_state']='ORAL_LAYER_PILOT_CONTACT_VISUAL_PENDING'
    bpy.context.scene['aevrynd_oral_motion_limit']=OPEN
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DST),compress=True)
    np.savez_compressed(S/'aevrynd-female-next-r0024-oral-fit-data.npz',**cache)
    save(LABEL+'-build-verification.json',{'source':str(src),'sourceSha256':sha(src),'output':str(DST),'outputSha256':sha(DST),'status':'BUILT_REQUIRES_REOPEN_CONTACT_VISUAL_REVIEW','objects':results,'sourceMeshGeometryUnchanged':True,'targetData':targets,'bodyOpenWeight':OPEN,'bodyOpenMaximumMoveM':float(np.linalg.norm(delta*OPEN,axis=1).max()),'attachmentBoundSkinMaximumMoveM':attachment_move,'sourceBodyGeometrySha256':source_hashes[body.name],'wallSeconds':time.time()-started,'limitations':['Complete lining integrity/contact not yet verified.','Rigid dental transform is fitted pose data, not a calibrated jaw hinge.','Continuous motion, canthus closure, hair dynamics/self, full body/clothes and engine remain unqualified.']})
    print('R0024_BUILD_DONE',json.dumps(results),flush=True)
if __name__=='__main__': main()
