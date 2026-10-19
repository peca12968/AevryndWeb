"""Bounded paired physical-scattering diagnostic for r39A; no promotion."""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
sp=importlib.util.spec_from_file_location('a39shade',Path(__file__).with_name('build-female-next-r0039-complete-guides.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
m=a.m;f=a.f;b=a.b;v=a.v;E=a.E
def main():
    start=time.time();rows=[]
    params=json.loads((E.parent/'r0013-envelope-hair/fibre-shading-diagnostic.json').read_text())['hairMaterialChanges']
    for label,path in [('before',a.SRC),('a-after',a.OUT)]:
        bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
        state=f.state();hair=bpy.data.objects[f.OLD];P,R=m.eval_arrays(hair)
        for mat,row in zip(hair.data.materials,params):
            nt=mat.node_tree;out=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeOutputMaterial')
            shader=nt.nodes.new('ShaderNodeBsdfHairPrincipled');shader.model='HUANG';shader.parametrization='MELANIN'
            for key,value in [('Melanin',row['melanin']),('Melanin Redness',row['melaninRedness']),('Roughness',row['roughness']),('Random Color',.12),('Random Roughness',.10)]:
                shader.inputs[key].default_value=value
            if 'Aspect Ratio' in shader.inputs:shader.inputs['Aspect Ratio'].default_value=1.
            info=nt.nodes.new('ShaderNodeHairInfo');nt.links.new(info.outputs['Random'],shader.inputs['Random']);nt.links.new(shader.outputs['BSDF'],out.inputs['Surface'])
        s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.max_bounces=6;s.cycles.transparent_max_bounces=8
        s.render.hair_type='CYLINDER';s.render.hair_subdiv=0;s.render.threads_mode='FIXED';s.render.threads=4
        p,r=m.eval_arrays(hair);assert np.array_equal(p,P) and np.array_equal(r,R)
        now=f.state();assert now['meshes']==state['meshes'] and now['materials']==state['materials'] and now['skinFields']==state['skinFields']
        b.camera('oblique');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=512;s.render.resolution_percentage=100
        s.render.filepath=str(E/(label+'-cycles-oblique.png'));before=time.time();bpy.ops.render.render(write_still=True)
        rows.append({'label':label,'source':str(path),'sourceSha256':b.sha(path),'positions':f.sha(P),'radii':f.sha(R),
          'camera':b.matrix(s.camera.matrix_world),'stage':v.stage(),'resolution':[512,512],'seconds':time.time()-before,
          'preservedBodyEyeTissueLashMeshesMaterialsAndSkinFields':True,'hairMaterialsOnlyIntentionalDiagnosticChange':params})
        a.save('paired-scattering-diagnostic.json',{'rows':rows,'scope':'Same Cycles/Huang settings on both source andA, same roots/counts/radii/lights/exposure/camera. Low-cost offline diagnostic only; no EEVEE/engine/dynamics equivalence or geometry gain by changing renderer.','seconds':time.time()-start})
    assert rows[0]['camera']==rows[1]['camera'] and rows[0]['stage']==rows[1]['stage'] and rows[0]['hairMaterialsOnlyIntentionalDiagnosticChange']==rows[1]['hairMaterialsOnlyIntentionalDiagnosticChange']
    print('R39_PAIRED_SCATTER_DONE',time.time()-start,flush=True)
if __name__=='__main__':main()
