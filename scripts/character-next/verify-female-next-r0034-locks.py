"""Reopen current sources, certify physical-width/display state and fair views.

All-child capsule evidence is inherited only after exact native array, matrix,
body topology/pose and primitive/subdivision equality. Additional opposite/back
views cover the new asymmetric whole-scalp groom.
"""
import bpy,importlib.util,json,time,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
spec=importlib.util.spec_from_file_location('f34',Path(__file__).with_name('build-female-next-r0034-lock-fibres.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);a=f.a;g=f.g
v32=g.module('v32','verify-female-next-r0032-registered-skin.py')

def material_state(names):return {n:[v32.material_signature(m) if m else None for m in bpy.data.objects[n].data.materials] for n in names}
def lights():return [(o.name,list(o.location),list(o.rotation_euler),list(o.scale),o.data.energy,list(o.data.color)) for o in bpy.context.scene.objects if o.type=='LIGHT']
def generic_arrays(d):
    sizes=[c.points_length for c in d.curves];assert len(set(sizes))==1;n=sizes[0];p=np.empty(len(d.points)*3,dtype='f4');d.position_data.foreach_get('vector',p);r=np.empty(len(d.points),dtype='f4');d.attributes['radius'].data.foreach_get('value',r);return p.reshape(-1,n,3),r.reshape(-1,n)
def hash_array(x):return hashlib.sha256(x.tobytes()).hexdigest()

def additional_views(label):
    scene=bpy.context.scene;c=scene.camera;rows=[]
    for view,loc in [('back',(0.,.90,g.b.HEAD+.02)),('opposite-oblique',(-.46,-.82,g.b.HEAD+.04))]:
        c.location=loc;c.rotation_euler=(Vector(g.b.TARGET)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=85;bpy.context.view_layer.update();scene.render.filepath=str(a.E/f'{label}-saved-{view}.png');bpy.ops.render.render(write_still=True)
        rows.append({'view':view,'light':'saved','cameraMatrix':g.b.matrix(c.matrix_world),'lens':c.data.lens,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'curvePrimitive':scene.render.hair_type,'hairSubdivision':scene.render.hair_subdiv,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'lights':lights()})
    g.b.camera('face');return rows

def main():
    start=time.time();f.c.configure();g.b.E=a.E;report=a.read('c-fibres-build.json');source=Path(report['output']);assert g.b.sha(source)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(a.SRC));names=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render];original={n:g.signature(bpy.data.objects[n]) for n in names};mats=material_state(names);cfg=g.b.config(bpy.context.scene);original_lights=lights()
    # Save a durable functional fallback with the old hairstyle's exact data,
    # so the physical-width repair survives even if new art is rejected.
    bpy.ops.wm.open_mainfile(filepath=str(f.CONTAINER));old=next(o for o in bpy.context.scene.objects if o.type=='CURVES' and not o.hide_render);old_name=old.name;old_p,old_r=generic_arrays(old.data);old_matrix=np.array(old.matrix_world);old_materials=[v32.material_signature(m) for m in old.data.materials];old_cache=np.load(a.ROOTS)
    assert g.b.sha(f.CONTAINER)=='7f959bb5dd6f04c347ae4f78cb9eac7f1cbbf2a7d91dd24e994c05e6817aaae1';assert not old.modifiers and all(x.value==1 for x in old.data.attributes['curve_type'].data)
    assert np.array_equal(old_p,old_cache['positions']) and np.array_equal(old_r,old_cache['radii']);assert {n:g.signature(bpy.data.objects[n]) for n in names}==original and material_state(names)==mats and lights()==original_lights
    bpy.context.scene.render.hair_type='STRIP';bpy.context.scene.render.hair_subdiv=0;g.b.camera('face');bpy.context.scene['AFN34_status']='PHYSICAL_WIDTH_FUNCTIONAL_BASELINE_NOT_HAIRSTYLE_ACCEPTANCE'
    corrected=a.S/'aevrynd-female-next-r0034-p-physical-width-baseline.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(corrected),compress=True);bpy.ops.wm.open_mainfile(filepath=str(corrected));cp,cr=generic_arrays(bpy.data.objects[old_name].data);assert np.array_equal(cp,old_p) and np.array_equal(cr,old_r) and np.array_equal(np.array(bpy.data.objects[old_name].matrix_world),old_matrix)
    old_extra=additional_views('r33-physical-wide');a.save('physical-baseline-saved-verification.json',{'output':str(corrected),'outputSha256':g.b.sha(corrected),'original':str(f.CONTAINER),'originalSha256':g.b.sha(f.CONTAINER),'allNativePointsRadiiAndWorldMatrixExact':True,'bodySkinEyesLightsExact':True,'positionsSha256':hash_array(cp),'radiiSha256':hash_array(cr),'curvePrimitive':'STRIP','hairSubdivision':0,'scope':'Functional width-fidelity repair only. Underlying old neutral physical capsule proof retains its original body/optic scope; old STRAND rendered footprint was not covered. Hair art, self, motion and runtime remain unqualified.'})
    bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;actual={n:g.signature(bpy.data.objects[n]) for n in names};assert actual==original and material_state(names)==mats and lights()==original_lights and g.b.config(scene)==cfg
    assert scene.render.hair_type=='STRIP' and scene.render.hair_subdiv==0
    native=[o for o in scene.objects if o.type=='CURVES' and not o.hide_render];assert len(native)==1;o=native[0];d=o.data;p,r=generic_arrays(d);assert len(d.curves)==12000 and p.shape==(12000,160,3) and all(x.value==1 for x in d.attributes['curve_type'].data);assert not o.modifiers and o.parent==bpy.data.objects[g.b.BODY]
    cache=np.load(Path(report['cache']));assert g.b.sha(Path(report['cache']))==report['cacheSha256'];assert np.array_equal(p,cache['positions']) and np.array_equal(r,cache['radii']);assert hash_array(p)==report['positionsSha256'] and hash_array(r)==report['radiiSha256'];assert np.array_equal(np.array(o.matrix_world),np.array(report['nativeMatrixWorld']));assert np.isfinite(p).all() and np.isfinite(r).all() and r.min()>0
    assert [v32.material_signature(m) for m in d.materials]==old_materials
    roots=cache['sourceRootIds'];assert np.array_equal(roots,np.arange(12000)) and np.array_equal(cache['rootTriangles'],old_cache['rootTriangles']) and np.array_equal(cache['rootBarycentric'],old_cache['rootBarycentric'])
    body=bpy.data.objects[g.b.BODY];v,t=g.b.evaluated(body,True);tri=v[t[cache['rootTriangles']]];skin=np.einsum('ni,nij->nj',cache['rootBarycentric'],tri);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None];expected=skin+normal*.00018
    mx=np.array(o.matrix_world);world=p.astype('f8')@mx[:3,:3].T+mx[:3,3];errors=np.linalg.norm(world[:,0]-expected,axis=1);assert errors.max()<1e-6
    # Preview must truly be the same subset, not a differently generated groom.
    preview=np.load(a.S/'aevrynd-female-next-r0034-c-preview-hair.npz');ids=preview['sourceRootIds'];preview_equal=np.array_equal(p[ids],preview['positions']) and np.array_equal(r[ids],preview['radii']);assert preview_equal
    controls=[]
    controls_report=a.read('c-master-controls.json')['centres']
    for row in controls_report:
        ctrl=bpy.data.objects['CTRL34_B_'+row['name']];sp=ctrl.data.splines[0];assert sp.type=='NURBS' and sp.order_u==4 and sp.use_endpoint_u
        K=np.array([list(x.co[:3]) for x in sp.points]);error=float(np.linalg.norm(K-np.array(row['knots']),axis=1).max());assert error<1e-6;controls.append({'name':ctrl.name,'points':len(K),'degree':3,'maximumStoredControlErrorM':error})
    assert len(controls)==24 and not bpy.data.libraries and not bpy.data.texts
    before=a.read('r33-physical-wide-renders.json')['rows'];after=a.read('c-fibres-renders.json')['rows'];keys=('view','light','cameraMatrix','lens','resolution','engine','viewTransform','look','exposure','gamma','lights','world','curvePrimitive','hairSubdivision');matched=len(before)==len(after)==6 and all({k:x[k] for k in keys}=={k:y[k] for k in keys} for x,y in zip(before,after));assert matched
    new_extra=additional_views('c-fibres');assert old_extra==new_extra;g.b.camera('face');scene.render.filepath=str(a.E/'c-reopened-face.png');bpy.ops.render.render(write_still=True)
    a.save('additional-matched-views.json',{'old':old_extra,'new':new_extra,'conditionsExactlyMatch':True,'scope':'Actual saved-light back and opposite-oblique for independent asymmetric full-scalp structure.'})
    result={'status':'PASS_REOPENED_DATA_AND_DISPLAY_FIDELITY' if report['bodyContact']['status']=='PASS_TESTED_STATIC_CAPSULES' and all(v.get('remainingCapsules',{}).get('status','PASS_TESTED_STATIC_CAPSULES')=='PASS_TESTED_STATIC_CAPSULES' for v in report['opticalContact'].values()) else 'FAIL_OR_UNRESOLVED_CONTACT','source':str(source),'sourceSha256':g.b.sha(source),'cache':report['cache'],'cacheSha256':report['cacheSha256'],'allOriginalNineMeshGeometryAndUVExact':actual,'allOriginalSkinAndEyeMaterialsExact':True,'sameSixFibreMaterialsAsComparison':True,'originalLightsExposureExact':True,'same12000PhysicalFollicles':True,'allNativePositionsRadiiAndMatrixExact':True,'previewExactlyMatchesFullSubset':preview_equal,'rootBindingMaximumErrorM':float(errors.max()),'editableIndependentCages':controls,'curvePrimitive':'STRIP','hairSubdivision':0,'completeEightViewPairedConditionsExact':True,'contactInheritance':{'basis':'All native positions, radii and world matrix match exact arrays tested against exact evaluated body/optics in full build. POLY +subdivision0 prevents curve overshoot; STRIP respects physical radius.','body':report['bodyContact'],'optical':report['opticalContact']},'functionalFallbackSource':str(corrected),'functionalFallbackSha256':g.b.sha(corrected),'externalLibraries':0,'seconds':time.time()-start,'limits':['Neutral body/optic finite capsules only; not hair/hair, self, motion, rig, cloth or runtime.','EEVEE preview material is not a calibrated anisotropic hair-scattering implementation.','Shape and appearance require separate multi-angle review; no automatic score or whole-character promotion.']};a.save('c-saved-lock-verification.json',result);print('R34_REOPENED_VERIFIED',result['status'],time.time()-start,flush=True)
if __name__=='__main__':main()
