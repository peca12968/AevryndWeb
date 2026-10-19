"""Paired offline scattering diagnostic, separate from EEVEE/engine evidence.

Same pinned Huang parameters as earlier material research on BOTH present-day
grooms. Geometry, source skin/optics, lighting, exposure and camera stay fixed.
Never substitute this Cycles reference for an Aevrynd runtime result.
"""
import bpy,importlib.util,json,time,hashlib
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('v34',Path(__file__).with_name('verify-female-next-r0034-locks.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);f=v.f;a=v.a;g=v.g

def main():
    start=time.time();f.c.configure();g.b.E=a.E;proof=a.read('c-saved-lock-verification.json');assert proof['status']=='PASS_REOPENED_DATA_AND_DISPLAY_FIDELITY'
    inherited=json.loads((a.E.parent/'r0013-envelope-hair/fibre-shading-diagnostic.json').read_text());params=inherited['hairMaterialChanges'];rows=[]
    for label,source in [('r33-scattering',Path(proof['functionalFallbackSource'])),('c-scattering',Path(proof['source']))]:
        bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;meshes={n:g.signature(bpy.data.objects[n]) for n in proof['allOriginalNineMeshGeometryAndUVExact']};skin_eye_materials=v.material_state(list(meshes));source_lights=v.lights();original_settings={'view':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma}
        native=next(o for o in scene.objects if o.type=='CURVES' and not o.hide_render);p,r=v.generic_arrays(native.data);matrix=np.array(native.matrix_world);point_hash=v.hash_array(p);radius_hash=v.hash_array(r)
        settings=[]
        for m,row in zip(native.data.materials,params):
            nt=m.node_tree;out=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeOutputMaterial');hair=nt.nodes.new('ShaderNodeBsdfHairPrincipled');hair.model='HUANG';hair.parametrization='MELANIN';hair.inputs['Melanin'].default_value=row['melanin'];hair.inputs['Melanin Redness'].default_value=row['melaninRedness'];hair.inputs['Roughness'].default_value=row['roughness'];hair.inputs['Random Color'].default_value=.12;hair.inputs['Random Roughness'].default_value=.10
            if 'Aspect Ratio' in hair.inputs:hair.inputs['Aspect Ratio'].default_value=1.
            info=nt.nodes.new('ShaderNodeHairInfo');nt.links.new(info.outputs['Random'],hair.inputs['Random']);nt.links.new(hair.outputs['BSDF'],out.inputs['Surface']);settings.append({'model':'HUANG','melanin':row['melanin'],'melaninRedness':row['melaninRedness'],'roughness':row['roughness'],'randomColor':.12,'randomRoughness':.10,'aspectRatio':1.})
        scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.max_bounces=8;scene.cycles.transparent_max_bounces=8;scene.render.hair_type='CYLINDER';scene.render.hair_subdiv=0;scene.render.threads_mode='FIXED';scene.render.threads=4
        assert {n:g.signature(bpy.data.objects[n]) for n in meshes}==meshes and v.material_state(list(meshes))==skin_eye_materials and v.lights()==source_lights
        pp,rr=v.generic_arrays(native.data);assert np.array_equal(pp,p) and np.array_equal(rr,r) and np.array_equal(np.array(native.matrix_world),matrix)
        g.b.camera('face');out=a.S/f'aevrynd-female-next-r0034-{label}-reference.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
        images=[]
        for view in ('oblique','profile'):
            g.b.camera(view);scene.render.filepath=str(a.E/f'{label}-{view}.png');before=time.time();bpy.ops.render.render(write_still=True);images.append({'view':view,'path':scene.render.filepath,'cameraMatrix':g.b.matrix(scene.camera.matrix_world),'lens':scene.camera.data.lens,'seconds':time.time()-before,'lights':source_lights,'display':original_settings})
        rows.append({'label':label,'source':str(source),'sourceSha256':g.b.sha(source),'output':str(out),'outputSha256':g.b.sha(out),'positionsSha256':point_hash,'radiiSha256':radius_hash,'allGeometrySkinEyesLightsExact':True,'hairMaterials':settings,'images':images})
        a.save('paired-scattering-reference.json',{'rows':rows,'renderEngine':'CYCLES','samples':24,'threads':4,'hairPrimitive':'CYLINDER','hairSubdivision':0,'parameterSource':'r0013/fibre-shading-diagnostic.json (same parameters on both grooms, not calibrated target pigment)','scope':'Offline material/geometry diagnostic only. Identical shape counts/material/light/exposure settings per pair. Not EEVEE equivalence, engine shader/runtime, dynamics or whole-character acceptance.','seconds':time.time()-start})
    assert rows[0]['hairMaterials']==rows[1]['hairMaterials']
    for x,y in zip(rows[0]['images'],rows[1]['images']):assert x['cameraMatrix']==y['cameraMatrix'] and x['lights']==y['lights'] and x['display']==y['display']
    print('R34_SCATTERING_PAIR_DONE',time.time()-start,flush=True)
if __name__=='__main__':main()
