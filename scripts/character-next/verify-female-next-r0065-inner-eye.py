"""Independent exact scope audit for the two-inner-material change.

Checks source geometry in seven previously qualified ocular poses, native
shapes/UVs/curves/material assignments and every original material. Reuses
only corresponding r60 static contact evidence; no new continuous claim.
"""
from pathlib import Path
import bpy,numpy as np,json,copy,time,sys,importlib.util
def module(n,p):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('eye65verifybuild','build-female-next-r0065-inner-eye.py');d=m.m;g=d.g;k=g.k;v=module('eye65signature','verify-female-next-r0061-complete-groom.py');E=m.E
POSES=[('neutral',0.,0.),('quarter',.25,.25),('half',.5,.5),('threeQuarter',.75,.75),('closed',1.,1.),('leftWink',1.,0.),('rightWink',0.,1.)]
def read(p):return json.loads(p.read_text(encoding='utf8'))
def geometry(names):
    ctrl=bpy.data.objects['AFN59_FACE_CONTROLS'];ctrl.animation_data.action=None;v.raise_subdivision();result={}
    for name,left,right in POSES:
        ctrl['blink_left']=left;ctrl['blink_right']=right;ctrl.update_tag();bpy.context.view_layer.update();rows={}
        for obname in names:
            row=k.mesh(bpy.data.objects[obname]);rows[obname]={field:v.digest(row[field]) for field in ('V','T','mi','nativeTriangleFace')}
        result[name]=rows
    return result
def main():
    tick=time.time();ref=read(E/'a-build-summary.json');path=m.OUT
    if '--history' in sys.argv:path=d.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/path.name
    assert g.sha(path)==ref['outputSha256'] and g.sha(m.SRC)==ref['sourceSha256'];names=list(read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values())
    bpy.ops.wm.open_mainfile(filepath=str(m.SRC));bpy.context.scene.frame_set(1);native={n:v.mesh_signature(bpy.data.objects[n]) for n in names};originalMaterials={mat.name:k.f.v.v32.material_signature(mat) for mat in bpy.data.materials if mat.use_nodes};curves={o.name:k.v59.native_curves(o) for o in bpy.data.objects if o.type=='CURVES'};visibility={o.name:[o.type,o.hide_render,o.hide_get()] for o in bpy.context.scene.objects if o.type in ('MESH','CURVES')};stage=k.f.v.stage();G0=geometry(names)
    bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);newNative={n:v.mesh_signature(bpy.data.objects[n]) for n in names};allowed={'AFN57_CANONICAL_IRIS':'AFN65_IMMERSED_IRIS_DIFFUSE_APPROX','AFN57_CANONICAL_PUPIL':'AFN65_ABSORBING_PUPIL_APPROX'};assignments=[]
    for name in names:
        before=copy.deepcopy(native[name]);after=copy.deepcopy(newNative[name]);assert {key:before[key] for key in ('native','keys','matrix')}=={key:after[key] for key in ('native','keys','matrix')}
        o=bpy.data.objects[name]
        for i,mat in enumerate(o.data.materials):
            if name in ('AFN60_L_IRIS_PUPIL_SURFACE','AFN60_R_IRIS_PUPIL_SURFACE') and mat.name in allowed.values():
                old=next(n for n,new in allowed.items() if new==mat.name);expected=copy.deepcopy(originalMaterials[old]);n=next(n for n in expected['nodes'] if n['type']=='ShaderNodeBsdfPrincipled');assert n['inputs']['Specular IOR Level']==.5;n['inputs']['Specular IOR Level']=0.;assert after['materials'][i]==expected;assignments.append({'object':name,'slot':i,'material':mat.name});after['materials'][i]=before['materials'][i]
        assert before==after
    assert len(assignments)==4;assert curves=={o.name:k.v59.native_curves(o) for o in bpy.data.objects if o.type=='CURVES'};assert visibility=={o.name:[o.type,o.hide_render,o.hide_get()] for o in bpy.context.scene.objects if o.type in ('MESH','CURVES')}
    assert originalMaterials=={n:k.f.v.v32.material_signature(bpy.data.materials[n]) for n in originalMaterials};now=k.f.v.stage();assert now['lights']==stage['lights']
    for name in ('transform','look','exposure','gamma','world'):assert now['config'][name]==stage['config'][name]
    images=[]
    for im in bpy.data.images:
        if im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();im.reload();images.append({'relative':im.filepath,'sha256':g.sha(p),'colorSpace':im.colorspace_settings.name})
    assert len(images)==15 and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    G1=geometry(names);assert G0==G1
    old=E.parent/'r0060-ocular-assembly';contact=read(old/'b-contact-verification.json');poses=read(old/'b-additional-pose-verification.json');space=read(old/'b-cavity-volume-verification.json');assert contact['sourceSha256']==poses['sourceSha256']==space['sourceSha256']==ref['sourceSha256'];assert contact['status']=='PASS_TWO_ENDPOINT_SURFACE_SCOPE_ONLY' and poses['status']=='PASS_SEVEN_TESTED_STATIC_POSES_ONLY'
    result={'status':'PASS_EXACT_INNER_MATERIAL_SCOPE_AND_GEOMETRY_TRANSFER','source':str(path),'sha256':g.sha(path),'originalSource':str(m.SRC),'originalSourceSha256':ref['sourceSha256'],'openedFromHistory':'--history' in sys.argv,'allFiveNativeMeshesShapeKeysUVMatricesExact':True,'allOriginalMaterialsPreservedExactly':True,'onlyTwoCopiedMaterialSpecularInputsChanged':True,'actualAssignments':assignments,'allNativeCurvesAndVisibilityExact':True,'originalLightsSkinExposureExact':True,'allSevenActualRenderGeometryHashesExact':G1,'maximumGeometryChangeM':0.,'relativeTextures':images,'automaticLibrariesOrFrameHandlers':False,'newControlsOrRigAuthored':False,'newGeometryContactTestsRun':False,'transferredContactScope':{'sourceStatus':poses['status'],'exactSourceSha256':ref['sourceSha256'],'evidence':['../r0060-ocular-assembly/b-contact-verification.json','../r0060-ocular-assembly/b-additional-pose-verification.json','../r0060-ocular-assembly/b-cavity-volume-verification.json'],'basis':'Exact actual V/T/material-index/native-face hashes in all seven corresponding poses; native keys/UVs/topology/matrices/visibility exact. Only specular lobe inputs change, with no alpha, transmission, displacement or volume changes.','notCertified':['Full body or adjacent self contacts outside old scope','Facial/head hair finite/self/root joins','Tissue thickness and complete lid sealing','Continuous time, head motion or cloth','Calibrated multi-interface eye optics','Engine runtime/performance'],'exactGlobalSignedMinimumM':None,'numericalAllowanceM':1e-6},'seconds':time.time()-tick};d.save('history-readback.json' if '--history' in sys.argv else 'a-functional-contact-transfer.json',result);print('R65_EXACT_SCOPE_PASS',len(G1),len(assignments),time.time()-tick,flush=True)
if __name__=='__main__':main()
