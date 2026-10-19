"""One physical hair-material dependency, with equal-Cycles controls.

Never present renderer change as a geometry/skin improvement. All comparison
inputs are rendered with the same fixed lights/exposure/Cycles settings.
No radius, density, colour or roughness sweep. The saved C source also carries
its real rest follicle lineage as editable native curve-domain attributes.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,math,sys
from mathutils import Vector
sp=importlib.util.spec_from_file_location('groom61shade',Path(__file__).with_name('build-female-next-r0061-surface-flow-groom.py'));g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
OUT=g.S/'aevrynd-female-next-r0061-c-physical-ponytail-study.blend'
NAME='AFN61_SCALP_ATTACHED_PONYTAIL_FIBRES'

def settings():
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.seed=61061;s.cycles.max_bounces=6;s.cycles.transparent_max_bounces=8
    s.render.threads_mode='FIXED';s.render.threads=4;s.render.hair_type='CYLINDER';s.render.hair_subdiv=0;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
    return {'engine':'CYCLES','device':'CPU','samples':24,'denoise':True,'threads':4,'hairPrimitive':'CYLINDER','hairSubdiv':0,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'viewTransform':s.view_settings.view_transform}

def render(tag,views):
    s=bpy.context.scene;rows=[]
    lights=[(o,list(o.location),list(o.rotation_euler),list(o.scale)) for o in s.objects if o.type=='LIGHT']
    for view in views:
        g.k.b.camera('profile' if view=='hair-profile' else ('oblique' if view in ('opposite-oblique','alternate-oblique','back') else view));s.camera.data.lens=85
        if view=='hair-profile':
            s.camera.location=(.93,-.01,1.43);s.camera.rotation_euler=(Vector((0,.03,1.405))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=65
        if view=='opposite-oblique':
            s.camera.location.x=-s.camera.location.x;s.camera.rotation_euler=(Vector(g.k.b.TARGET)-s.camera.location).to_track_quat('-Z','Y').to_euler()
        if view=='alternate-oblique':
            for o,loc,rot,scale in lights:o.location.x=-o.location.x;o.rotation_euler=(Vector(g.k.b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
        if view=='back':
            s.camera.location=(0,.91,1.43);s.camera.rotation_euler=(Vector((0,.02,1.405))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=65
        s.render.filepath=str(g.E/f'{tag}-{view}.png');bpy.context.view_layer.update()
        recovered='--recover-controls' in sys.argv and Path(s.render.filepath).exists()
        if not recovered:bpy.ops.render.render(write_still=True)
        rows.append({'file':s.render.filepath,'view':view,'camera':np.array(s.camera.matrix_world).tolist(),'settings':settings(),'completedImageRecoveredWithoutRerender':recovered})
        for o,loc,rot,scale in lights:o.location=loc;o.rotation_euler=rot;o.scale=scale
        bpy.context.view_layer.update()
    return rows

def main():
    tick=time.time();ref=json.loads((g.E/'b-fibres-build-summary.json').read_text());src=Path(ref['output']);assert g.sha(src)==ref['outputSha256']
    if '--continue' in sys.argv or '--recover-controls' in sys.argv:
        row=json.loads((g.E/'c-build-summary.json').read_text());assert g.sha(OUT)==row['outputSha256']
        # Equal-engine controls: source baseline and material-only B comparison.
        bpy.ops.wm.open_mainfile(filepath=str(g.SRC));settings();baseline=render('baseline-cycles',('face','body-face'))
        bpy.ops.wm.open_mainfile(filepath=str(src));settings();control=render('b-material-control-cycles',('face',))
        bpy.ops.wm.open_mainfile(filepath=str(OUT));settings();extra=render('c-physical',('alternate-oblique','hair-profile','body-face','back'))
        g.save('c-equal-renderer-controls.json',{'baseline':baseline,'sameGroomOldMaterial':control,'candidateAdditionalViews':extra,'rendererChangeCountsAsGeometryOrSkinImprovement':False,'seconds':time.time()-tick})
        return
    assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(src));o=bpy.data.objects[NAME];P=np.empty(len(o.data.position_data)*3,'f4');o.data.position_data.foreach_get('vector',P);oldHash=g.sha(src)
    raw=np.load(g.E/'b-fibres-authoring.npz');attrs=[('AFN61_RestRenderTriangle','INT',raw['rootTriangles'],'value'),('AFN61_NativeScalpFace','INT',raw['rootNativeFaces'],'value'),('AFN61_RestBarycentric','FLOAT_VECTOR',raw['rootBarycentric'].astype('f4'),'vector')]
    for name,kind,data,field in attrs:o.data.attributes.new(name,kind,'CURVE').data.foreach_set(field,data.ravel())
    o['AFN61_attachment']='Exact rest render-triangle/barycentric + original native face lineage stored on each curve. No deforming follower/hair physics yet; first follicle join remains unaccepted.'
    mat=bpy.data.materials.new('AFN61_CHIANG_MELANIN_HAIR');mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial');hair=t.nodes.new('ShaderNodeBsdfHairPrincipled');hair.model='CHIANG';hair.parametrization='MELANIN'
    values={'Melanin':.65,'Melanin Redness':.20,'Roughness':.38,'Radial Roughness':.36,'IOR':1.55,'Random Color':.12,'Random Roughness':.08}
    for name,value in values.items():hair.inputs[name].default_value=value
    info=t.nodes.new('ShaderNodeHairInfo');t.links.new(info.outputs['Random'],hair.inputs['Random']);t.links.new(hair.outputs[0],out.inputs['Surface']);o.data.materials.clear();o.data.materials.append(mat)
    Pafter=np.empty_like(P);o.data.position_data.foreach_get('vector',Pafter);assert np.array_equal(P,Pafter);s=settings();g.k.b.camera('face');bpy.context.preferences.filepaths.save_version=0
    bpy.context.scene['AFN61_status']='PHYSICAL_HAIR_LOOKDEV_NO_FULL_CONTACT_OR_RUNTIME_ACCEPTANCE';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    g.save('c-build-summary.json',{'source':str(src),'sourceSha256':oldHash,'output':str(OUT),'outputSha256':g.sha(OUT),'sameGeometryRadiiAndFolliclesAsB':True,'nativeRootMetadataStored':True,'hairShader':'Principled Hair BSDF / Chiang / Melanin','values':values,'settings':s,'materialReference':'https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/hair_principled.html','rendererScope':'Offline Blender/Cycles physical hair look development; not an Aevrynd renderer implementation or engine acceptance. Equal-Cycles baseline/control render required before an appearance decision.'})
    render('c-physical',('face','profile'));print('R61_PHYSICAL_HAIR_PILOT',time.time()-tick,flush=True)
if __name__=='__main__':main()
