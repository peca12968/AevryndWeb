"""Independent editable selection layers and saved closeup controls.

Groups are authoring selections, not rig weights or live deform controls.
Accept this review file only if adding them preserves every evaluated point.
"""
import bpy,importlib.util,json,time,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
spec=importlib.util.spec_from_file_location('v35',Path(__file__).with_name('verify-female-next-r0035-lid-rest.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);i=v.i;g=v.g;b=v.b;E=v.E

def main():
    proof=v.read('b-saved-rest-verification.json');assert proof['status']=='PASS_REOPENED_NEUTRAL_REST_SCOPE';source=Path(proof['source']);assert b.sha(source)==proof['sourceSha256'];b.E=E
    # Record actual closeup camera/width/light controls for reopened sources.
    rows=[]
    for label,path in [('before-reopened',Path(proof['originalSource'])),('b-after-reopened',source)]:
        bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;c=s.camera;c.location=(0,-.45,1.461);c.rotation_euler=(Vector((0,-.1125,1.45949))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=1400;s.render.resolution_y=650;s.render.filepath=str(E/(label+'-eyes.png'));bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
        rows.append({'label':label,'path':s.render.filepath,'sourceSha256':b.sha(path),'cameraMatrix':b.matrix(c.matrix_world),'lens':c.data.lens,'resolution':[1400,650],'primitive':s.render.hair_type,'hairSubdivision':s.render.hair_subdiv,'stage':v.stage()})
    assert all(rows[0][key]==rows[1][key] for key in ('cameraMatrix','lens','resolution','primitive','hairSubdivision','stage'));v.save('b-reopened-closeup-controls.json',{'rows':rows,'conditionsExactlyMatch':True})
    bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;original=v.visible_state();names=list(original);materials=v.materials(names);fields=v.fields(bpy.data.objects[b.BODY]);stage=v.stage();hair=next(o for o in s.objects if o.type=='CURVES' and not o.hide_render);hp,hr=v.hair_arrays(hair);hm=np.array(hair.matrix_world);body=bpy.data.objects[b.BODY];raw=np.array([list(p.co) for p in body.data.vertices]);patches=v.read('b-rest-patch-targets.json');delta=np.load(b.S/'aevrynd-female-next-r0035-a-native-lid-delta.npz')
    after=delta['nativeAfterLocal'];before=delta['nativeBeforeLocal'];assert np.array_equal(raw,after);displacement=np.linalg.norm(after-before,axis=1);groups=[];fixed_union=set()
    for side,patch in patches.items():
        moving=set(patch['upperMovingRimHandles']);fixed=set(patch['fixedBoundaryVertices'])|(set(patch['allFrontRimHandles'])-moving);fixed_union|=fixed
        selections={'UpperLidTissue':{vi:float(displacement[vi]/displacement.max()) for vi in patch['domainVertices'] if displacement[vi]>1e-10},'UpperLidRim':{row['vertex']:float(row['weight']) for row in patch['handleTargets'] if row['weight']>0},'PinnedLidBoundary':{vi:1. for vi in fixed}}
        for purpose,weights in selections.items():
            name=f'AFN35_{purpose}.{side}';group=body.vertex_groups.new(name=name)
            for vi,weight in weights.items():group.add([int(vi)],weight,'REPLACE')
            groups.append({'name':name,'purpose':'Editable authoring selection only; not calibrated skinning or animation','vertices':len(weights),'indices':sorted(weights)})
    assert not fixed_union&set(proof['nativeChangedVertices']);assert np.array_equal(raw[np.array(sorted(fixed_union))],before[np.array(sorted(fixed_union))])
    bpy.context.view_layer.update();assert v.visible_state()==original and v.materials(names)==materials and v.fields(body)==fields and v.stage()==stage
    s['AFN35_status']='PARTIAL_NATIVE_NEUTRAL_REST_REVIEW_STATIC_SCOPE_ONLY';s['AFN35_layer_note']='AFN35_* vertex groups select native rim/tissue/pinned boundary; no live rig, gaze or blink claim';b.camera('face');s.camera.data.lens=85
    out=b.S/'aevrynd-female-next-r0035-b-neutral-rest-review.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True);bpy.ops.wm.open_mainfile(filepath=str(out));assert v.visible_state()==original and v.materials(names)==materials and v.fields(bpy.data.objects[b.BODY])==fields and v.stage()==stage
    current_hair=next(o for o in bpy.context.scene.objects if o.type=='CURVES' and not o.hide_render);pp,rr=v.hair_arrays(current_hair);assert np.array_equal(pp,hp) and np.array_equal(rr,hr) and np.array_equal(np.array(current_hair.matrix_world),hm)
    for row in groups:assert row['name'] in bpy.data.objects[b.BODY].vertex_groups
    v.save('b-review-layer-verification.json',{'status':'PASS_REOPENED_EXACT_GEOMETRY_AUTHORING_GROUPS','source':str(source),'sourceSha256':b.sha(source),'output':str(out),'outputSha256':b.sha(out),'allNineEvaluatedMeshSignaturesExact':original,'skinFieldsAndAllMeshMaterialsExact':True,'allHairPositionsRadiiWorldMatrixExact':True,'stageAndWidthPolicyExact':True,'groups':groups,'nativePinnedBoundaryVerticesExact':True,'contactInheritance':'Exact evaluated geometry, hair, pose and width match b-saved-rest-verification.json, so its stated neutral scope applies. Groups do not implement rigging or dynamic constraints.','limits':proof['limits']});print('R35_REVIEW_LAYERS_DONE',len(groups),flush=True)
if __name__=='__main__':main()
