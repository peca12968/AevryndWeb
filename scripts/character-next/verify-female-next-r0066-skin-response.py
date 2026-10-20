"""Reopen the whole skin candidate and verify exact affected material scope.

Actual seven rendered pose geometries are compared with the qualified r65
hashes. This transfers only the already limited static ocular contact scope.
"""
from pathlib import Path
import bpy, numpy as np, json, copy, time, sys
import importlib.util
def module(n,p):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
b=module('skin66buildverify','build-female-next-r0066-skin-response.py');v65=module('skin66oldverify','verify-female-next-r0065-inner-eye.py');v=v65.v;k=b.k;E=b.E
def main():
    tick=time.time();ref=b.read(E/'a-build-summary.json');path=b.OUT
    if '--history' in sys.argv:path=b.m.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/path.name
    assert b.m.sha(path)==ref['outputSha256'] and b.m.sha(b.SRC)==ref['sourceSha256']==b.m.SOURCE_SHA
    names=list(b.read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values())
    bpy.ops.wm.open_mainfile(filepath=str(b.SRC));bpy.context.scene.frame_set(1)
    native={n:v.mesh_signature(bpy.data.objects[n]) for n in names};materials={m.name:k.f.v.v32.material_signature(m) for m in bpy.data.materials if m.use_nodes}
    curves={o.name:k.v59.native_curves(o) for o in bpy.data.objects if o.type=='CURVES'};stage=k.f.v.stage();visibility={o.name:[o.type,o.hide_render,o.hide_get()] for o in bpy.context.scene.objects if o.type in ('MESH','CURVES')}
    expected=copy.deepcopy(materials['AFN57_CANONICAL_SKIN'])
    for change in ref['changes']:
        if 'property' in change:continue
        n=next(n for n in expected['nodes'] if n['name']==change['node']);value=change['after'];n['inputs'][change['input']]=np.asarray(value,dtype='f4').tolist()
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1)
    actual=k.f.v.v32.material_signature(bpy.data.materials['AFN66_SOURCE_HEIGHT_AND_SKIN_TRANSPORT']);assert actual==expected
    newMat=bpy.data.materials['AFN66_SOURCE_HEIGHT_AND_SKIN_TRANSPORT'];assert newMat.node_tree.nodes['Principled BSDF'].subsurface_method=='RANDOM_WALK_SKIN'
    assert all(not x.is_linked for x in newMat.node_tree.nodes['Material Output'].inputs if x.name in ('Displacement','Volume'))
    assigned=[]
    for name in names:
        after=v.mesh_signature(bpy.data.objects[name]);before=native[name]
        assert {key:before[key] for key in ('native','keys','matrix')}=={key:after[key] for key in ('native','keys','matrix')}
        for i,mat in enumerate(bpy.data.objects[name].data.materials):
            if mat.name=='AFN66_SOURCE_HEIGHT_AND_SKIN_TRANSPORT':assert after['materials'][i]==expected;after['materials'][i]=before['materials'][i];assigned.append({'object':name,'slot':i})
        assert before==after
    assert sorted((x['object'],x['slot']) for x in assigned)==sorted((x['object'],x['slot']) for x in ref['assignments'])
    assert materials=={n:k.f.v.v32.material_signature(bpy.data.materials[n]) for n in materials}
    assert curves=={o.name:k.v59.native_curves(o) for o in bpy.data.objects if o.type=='CURVES'}
    assert visibility=={o.name:[o.type,o.hide_render,o.hide_get()] for o in bpy.context.scene.objects if o.type in ('MESH','CURVES')}
    now=k.f.v.stage();assert now['lights']==stage['lights'] and now['config']==stage['config']
    images=[]
    for im in bpy.data.images:
        if im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();im.reload();images.append({'relative':im.filepath,'sha256':b.m.sha(p),'colorSpace':im.colorspace_settings.name})
    assert len(images)==15 and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    history='--history' in sys.argv
    if history:
        local=b.read(E/'a-native-readback.json');assert local['sha256']==ref['outputSha256'];G=local['allSevenActualRenderGeometryHashesExact']
    else:G=v65.geometry(names)
    prior=b.read(E.parent/'r0065-eye-shading/a-functional-contact-transfer.json');assert prior['sha256']==ref['sourceSha256'] and prior['maximumGeometryChangeM']==0 and G==prior['allSevenActualRenderGeometryHashesExact']
    result={'status':'PASS_EXACT_SKIN_MATERIAL_SCOPE_STATIC_GEOMETRY_PRESERVED','source':str(path),'sha256':b.m.sha(path),'baselineSource':str(b.SRC),'baselineSha256':ref['sourceSha256'],'openedFromHistory':'--history' in sys.argv,'allFiveNativeGeometryKeysUVMatricesExact':True,'allOriginalMaterialsAndR65EyeGainPreserved':True,'newMaterialMatchesOnlyDeclaredSkinResponseChanges':True,'sourceSkinTransportApproximationNotCalibratedOptics':True,'allCurvesVisibilityLightingExposureExact':True,'pigmentRoughnessTextureRoutingExact':True,'relativeTextures':images,'allSevenActualRenderGeometryHashesExact':G,'maximumGeometryChangeM':0.,'transferredContactScope':prior['transferredContactScope'],'newContactTestsRun':False,'continuousFullBodyHairClothContactsAccepted':False,'fullCharacterRigOrRuntimeAccepted':False,'seconds':time.time()-tick}
    result['sevenPosesReevaluatedThisRun']=not history
    result['historyPoseEvidenceBasis']='Seven local actual pose hashes transferred by identical .blend bytes and all 15 identical relative textures; history reopen verifies native data/materials/images without redundant pose rerun.' if history else 'Seven actual candidate render-level poses evaluated in this run.'
    b.m.save('history-readback.json' if history else 'a-native-readback.json',result);print('R66_READBACK_PASS',len(G),len(assigned),time.time()-tick,flush=True)
if __name__=='__main__':main()
