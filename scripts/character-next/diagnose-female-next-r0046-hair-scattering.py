"""One controlled paired hair-scattering diagnostic after two rejected styles.
Same physical lighting/camera/exposure/radii. Geometry untouched in each file.
Not a geometry improvement, target engine shader, or character acceptance.
"""
import bpy,importlib.util,time,json,hashlib
from pathlib import Path
sp=importlib.util.spec_from_file_location('crop46diag',Path(__file__).with_name('build-female-next-r0046-textured-crop.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
E=a.E;b=a.b;f=a.f;v=a.v;S=a.S
def main():
    tick=time.time();rows=[]
    for tag,path in [('baseline-r42b',a.SRC),('rejected-b',S/'aevrynd-female-next-r0046-b-explicit-tuft-crop.blend')]:
        bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;hair=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];before=f.state();original=list(hair.data.materials);mp=[]
        for old in original:
            color=None
            for n in old.node_tree.nodes:
                if n.type=='BSDF_PRINCIPLED':color=tuple(n.inputs['Base Color'].default_value);break
            assert color is not None,('No direct original color',old.name)
            mat=bpy.data.materials.new('AFN46_DIAGNOSTIC_HAIR_'+old.name);mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfHairPrincipled');bs.model='CHIANG';bs.parametrization='COLOR';bs.inputs['Color'].default_value=color;bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.30;bs.inputs['IOR'].default_value=1.55;nt.links.new(bs.outputs[0],out.inputs['Surface']);mp.append({'original':old.name,'diagnostic':mat.name,'sameLinearColorInput':color,'model':'CHIANG','parametrization':'COLOR','roughness':.35,'radialRoughness':.30,'ior':1.55})
        hair.data.materials.clear()
        for row in mp:hair.data.materials.append(bpy.data.materials[row['diagnostic']])
        s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.cycles.device='CPU';shapes=[x.identifier for x in s.render.bl_rna.properties['hair_type'].enum_items];assert 'CYLINDER' in shapes;s.render.hair_type='CYLINDER';s.render.hair_subdiv=0;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;b.camera('face');s.camera.data.lens=85;s.render.filepath=str(E/f'{tag}-cycles-hair-face.png');bpy.context.view_layer.update();stage={'cameraMatrix':b.matrix(s.camera.matrix_world),'lens':s.camera.data.lens,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'transform':s.view_settings.view_transform,'gamma':s.view_settings.gamma,'lights':before['stage']['lights'],'resolution':[800,800],'engine':'CYCLES','samples':32,'denoising':False,'curveShape':'CYLINDER','hairSubdivision':0,'materials':mp};bpy.ops.render.render(write_still=True)
        after=f.state();assert after['meshes']==before['meshes'] and after['skinFields']==before['skinFields'] and after['materials']==before['materials'];assert all(after['curves'][n]==row for n,row in before['curves'].items() if n!=hair.name);assert after['curves'][hair.name]['positions']==before['curves'][hair.name]['positions'] and after['curves'][hair.name]['radii']==before['curves'][hair.name]['radii'];rows.append({'tag':tag,'source':str(path),'sourceSha256':b.sha(path),'ownGeometryNativeWidthsSkinUnchanged':True,'settings':stage})
        a.save('hair-scattering-diagnostic.json',{'status':'PAIRED_ACTUAL_3D_RENDERS_REQUIRE_VISUAL_INTERPRETATION','rows':rows,'scope':'Controlled offline hair material+round-cross-section renderer diagnosis, not new geometry/natural hair motion or engine-appearance qualification','seconds':time.time()-tick})
    keys=('cameraMatrix','lens','exposure','look','transform','gamma','lights','resolution','engine','samples','denoising','curveShape');assert all(rows[0]['settings'][k]==rows[1]['settings'][k] for k in keys);a.save('hair-scattering-diagnostic.json',{'status':'PASS_MATCHED_DIAGNOSTIC_CONDITIONS_NOT_CHARACTER_ACCEPTANCE','rows':rows,'scope':'Both sources rendered using identical hair scattering/round cross-section and physical stage; per-source geometry/native widths/skin held. No runtime shader or complete hair acceptance.','seconds':time.time()-tick});print('R46_PAIRED_SCATTERING_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
