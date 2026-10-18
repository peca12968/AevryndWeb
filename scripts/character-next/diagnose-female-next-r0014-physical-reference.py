"""Same Huang parameters as r0013 C; inspect the changed groom in a second renderer."""
import bpy,json,importlib.util,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-female-next-r0014-scalp-flow.py'));verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
flow=verify.flow;E,S=flow.E,flow.S
def geometry():
    import hashlib
    h=hashlib.sha256()
    for o in sorted((o for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN14_')),key=lambda o:o.name):
        P,rr=verify.prior.native_paths(o)
        for p,r in zip(P,rr):h.update(p.tobytes());h.update(r.tobytes())
    return h.hexdigest()
def main():
    clumped='--clumped' in sys.argv;prefix='c-' if clumped else '';src=S/('aevrynd-female-next-r0014-c-clump-volume-study.blend' if clumped else 'aevrynd-female-next-r0014-a-scalp-flow-study.blend');proof=json.loads((E/(prefix+'saved-scalp-flow-verification.json')).read_text());assert flow.route.sha(src)==proof['candidateSha256'] and proof['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE'
    bpy.ops.wm.open_mainfile(filepath=str(src));before=verify.original();geo=geometry();scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.cycles.seed=1313;scene.render.threads_mode='FIXED';scene.render.threads=6
    settings=json.loads((flow.R/'Evidence/character-female-next/r0013-envelope-hair/fibre-shading-diagnostic.json').read_text())['hairMaterialChanges']
    for row in settings:
        m=bpy.data.materials[row['material']];nodes=m.node_tree.nodes;out=next(n for n in nodes if n.bl_idname=='ShaderNodeOutputMaterial');hair=nodes.new('ShaderNodeBsdfHairPrincipled');hair.model=row['model'];hair.parametrization='MELANIN';hair.inputs['Melanin'].default_value=row['melanin'];hair.inputs['Melanin Redness'].default_value=row['melaninRedness'];hair.inputs['Roughness'].default_value=row['roughness'];hair.inputs['Random Color'].default_value=.12;hair.inputs['Random Roughness'].default_value=.1;info=nodes.new('ShaderNodeHairInfo');m.node_tree.links.new(info.outputs['Random'],hair.inputs['Random']);m.node_tree.links.new(hair.outputs['BSDF'],out.inputs['Surface'])
    assert geometry()==geo and verify.original()==before
    views=('face','oblique') if clumped else ('face','oblique','profile');label='c-huang-clump-reference' if clumped else 'b-huang-scalp-flow-reference';fits=flow.solid.stage.eyes.helper_centres();images=[flow.solid.stage.eyes.render(label,v,fits,'neutral') for v in views]
    dest=S/('aevrynd-female-next-r0014-c-huang-clump-reference.blend' if clumped else 'aevrynd-female-next-r0014-b-huang-scalp-flow-reference.blend');scene['aevrynd_release_state']='SAME_GEOMETRY_OFFLINE_MATERIAL_REFERENCE_NOT_RUNTIME';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/(prefix+'physical-reference.json')).write_text(json.dumps({'source':str(src),'sourceSha256':flow.route.sha(src),'output':str(dest),'outputSha256':flow.route.sha(dest),'geometryUnchangedSha256':geo,'originalHeadStateUnchanged':True,'hairSettingsSource':'r0013/fibre-shading-diagnostic.json','sameHuangParametersAsR0013C':True,'baselineImages':['r0013/c-huang-reference-'+v+'-neutral.png' for v in views],'renders':images,'renderer':'CYCLES','samples':32,'threads':6,'scope':'Second-renderer robustness check against r0013 C with the same material parameters; not an Aevrynd runtime shader or a face/anatomy improvement claim.','overallCharacterScore':None},indent=2)+'\n');print('AFN14_PHYSICAL_REFERENCE_DONE',flush=True)
if __name__=='__main__':main()
