"""Independent reopen of the complete Eve study and unchanged r65 anatomy."""
from pathlib import Path
import bpy,numpy as np,time,sys,importlib.util
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('eve67verifybuild','build-female-next-r0067-native-eve.py');v=module('eve67verifysig','verify-female-next-r0061-complete-groom.py');k=m.k
def main():
    tick=time.time();ref=m.read(m.E/'b-build-summary.json');path=Path(ref['output']);history='--history' in sys.argv
    if history:path=m.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/path.name
    assert m.m.sha(path)==ref['outputSha256'] and m.m.sha(m.SRC)==m.SOURCE_SHA
    names=list(m.read(m.E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());bpy.ops.wm.open_mainfile(filepath=str(m.SRC));bpy.context.scene.frame_set(1)
    before={n:v.mesh_signature(bpy.data.objects[n]) for n in names};mats={mat.name:k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};curves={o.name:k.v59.native_curves(o) for o in bpy.data.objects if o.type=='CURVES'};visibility={o.name:[o.type,o.hide_render,o.hide_get()] for o in bpy.context.scene.objects if o.type in ('MESH','CURVES')};stage=k.f.v.stage()
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);assert before=={n:v.mesh_signature(bpy.data.objects[n]) for n in names};assert mats=={n:k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert curves=={n:k.v59.native_curves(bpy.data.objects[n]) for n in curves}
    for name,vis in visibility.items():
        o=bpy.data.objects[name];expected=[vis[0],True,True] if name=='AFN57_CANONICAL_BOB_GUIDES' else vis;assert [o.type,o.hide_render,o.hide_get()]==expected
    assert k.f.v.stage()==stage
    hair=bpy.data.objects[ref['completeCurveObject']];emitter=bpy.data.objects['AFN67_ORIGINAL_FEMALE_EVE_EMITTER'];assert not hair.hide_render and emitter.hide_render and emitter.hide_get() and len(hair.modifiers)==0 and len(emitter.particle_systems)==1
    P,counts,radius=m.curve_arrays(hair);raw=np.load(m.E/'b-converted-eve-data.npz');assert np.array_equal(P,raw['positions']) and np.array_equal(counts,raw['counts']) and np.array_equal(radius,raw['radii']) and np.array_equal(np.array(hair.matrix_world),raw['matrix']);assert np.isfinite(P).all() and np.isfinite(radius).all() and (radius>=0).all()
    assert len(counts)==m.read(m.E/'native-eve-inspection.json')['evaluatedChildren'];ends=np.cumsum(counts)-1;nonends=np.ones(len(P),dtype=bool);nonends[ends]=False;source=emitter.particle_systems[0].settings;nominal=source.root_radius*source.radius_scale*.5;assert source.root_radius==source.tip_radius and source.use_close_tip and np.all(radius[nonends]==np.float32(nominal)) and np.all(radius[ends]==0.)
    assert hair.data.materials[0]==bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'].data.materials[0] and np.array_equal(np.array(emitter.matrix_world),np.array(bpy.data.objects[names[4]].matrix_world))
    images=[]
    for im in bpy.data.images:
        if im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();im.reload();images.append({'relative':im.filepath,'sha256':m.m.sha(p),'colorSpace':im.colorspace_settings.name})
    assert len(images)==15 and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    v.raise_subdivision();prior=m.read(m.E.parent/'r0065-eye-shading/a-functional-contact-transfer.json');assert prior['sha256']==m.SOURCE_SHA;G={}
    for name in names:
        row=k.mesh(bpy.data.objects[name]);G[name]={field:v.digest(row[field]) for field in ('V','T','mi','nativeTriangleFace')}
    assert G==prior['allSevenActualRenderGeometryHashesExact']['neutral']
    result={'status':'PASS_NATIVE_FULL_CURVE_READBACK_NOT_CONTACT_ACCEPTANCE','source':str(path),'sha256':m.m.sha(path),'openedFromHistory':history,'baselineSourceSha256':m.SOURCE_SHA,'originalFiveComponentsAllKeysUVMatricesAndMaterialsExact':True,'originalCurvesGeometryExact':True,'intentionalVisibilityChange':'Only original sparse Bob hidden; new Eve visible, native emitter hidden.','newNativeCurves':len(counts),'newNativePoints':len(P),'renderGeometryMatchesBakedData':True,'radiusTransfer':'Unedited author diameter * diameter scale /2, original close-tip0; no collision-driven shrink.','maximumLocalRadiusM':float(radius.max()),'zeroRadiusTips':int((radius==0).sum()),'originalStageSkinEyeGainExposureExact':True,'actualNeutralBodyOcularGeometryHashesExact':G,'relativeTextures':images,'nativeConversionGeometryDoesNotProveStyleOrPhysics':True,'newBodyOrFaceRigOrHairDynamics':False,'automaticLibrariesHandlersOrAddons':False,'fullBodyHairRootSelfContinuousOrRuntimeAccepted':False,'seconds':time.time()-tick};m.m.save('history-readback.json' if history else 'b-native-readback.json',result);print('R67_NATIVE_REOPEN_PASS',len(counts),len(P),time.time()-tick,flush=True)
if __name__=='__main__':main()
