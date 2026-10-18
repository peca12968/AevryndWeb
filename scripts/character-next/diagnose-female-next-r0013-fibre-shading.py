"""Same-geometry/same-Cycles material comparison; never a substitute for engine proof."""
import bpy,json,importlib.util,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-female-next-r0013-native-groom.py'));verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
route=verify.route;E,S=route.E,route.S

def geometry():
    import hashlib
    h=hashlib.sha256()
    for o in sorted((o for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN13_')),key=lambda o:o.name):
        P,rr=verify.native_paths(o);h.update(o.name.encode())
        for p,r in zip(P,rr):h.update(p.tobytes());h.update(r.tobytes())
    return h.hexdigest()

def main():
    proof=json.loads((E/'b-resolved-static-verification.json').read_text());assert proof['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE'
    src=S/'aevrynd-female-next-r0013-b-native-envelope-hair-study.blend';assert route.sha(src)==proof['candidateSha256']
    bpy.ops.wm.open_mainfile(filepath=str(src));before=verify.original_state();geo=geometry();scene=bpy.context.scene;route.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');route.solid.stage.eyes.E=E;fits=route.solid.stage.eyes.helper_centres()
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=8;scene.cycles.seed=1313
    start=time.time();baseline=route.solid.stage.eyes.render('b-cycles-standard-bsdf','face',fits,'neutral')
    changes=[]
    for i,m in enumerate(sorted((m for m in bpy.data.materials if m.name.startswith('AFN13_ChestnutKeratin')),key=lambda m:m.name)):
        nodes=m.node_tree.nodes;out=next(n for n in nodes if n.bl_idname=='ShaderNodeOutputMaterial');hair=nodes.new('ShaderNodeBsdfHairPrincipled');hair.model='HUANG';hair.parametrization='MELANIN';hair.inputs['Melanin'].default_value=.68+.012*i;hair.inputs['Melanin Redness'].default_value=.25;hair.inputs['Roughness'].default_value=.36;hair.inputs['Random Color'].default_value=.12;hair.inputs['Random Roughness'].default_value=.1
        info=nodes.new('ShaderNodeHairInfo');m.node_tree.links.new(info.outputs['Random'],hair.inputs['Random']);m.node_tree.links.new(hair.outputs['BSDF'],out.inputs['Surface']);changes.append({'material':m.name,'model':'HUANG','melanin':.68+.012*i,'melaninRedness':.25,'roughness':.36})
    renders=[route.solid.stage.eyes.render('c-huang-reference',v,fits,'neutral') for v in ('face','oblique','profile')]
    after=verify.original_state();assert before==after;assert geometry()==geo
    scene['aevrynd_revision']='female-next-r0013-c-huang-reference';scene['aevrynd_release_state']='OFFLINE_MATERIAL_REFERENCE_NOT_RUNTIME'
    dest=S/'aevrynd-female-next-r0013-c-huang-reference.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    (E/'fibre-shading-diagnostic.json').write_text(json.dumps({'source':str(src),'sourceSha256':route.sha(src),'output':str(dest),'outputSha256':route.sha(dest),'sameNativeHairGeometrySha256':geo,'originalStateUnchanged':True,'renderEngine':'CYCLES','samples':32,'threads':8,'baselineSameRenderer':baseline,'candidateRenders':renders,'hairMaterialChanges':changes,'lightingExposureCameraUnchangedForPairedFace':True,'wallSeconds':time.time()-start,'status':'VISUAL_REVIEW_PENDING','references':['https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/hair_principled.html','https://docs.blender.org/api/5.2/bpy.types.Curves.html'],'limits':['Huang material is a Cycles-only offline reference, not an Aevrynd shader or runtime result.','Hair geometry and sampled-static collision scope inherited from exact B source; no dynamic or hair/hair proof.','Material appearance is not evidence of anatomical or geometry improvement.']},indent=2)+'\n');print('AFN13_FIBRE_DIAGNOSTIC_DONE',flush=True)

if __name__=='__main__':main()
