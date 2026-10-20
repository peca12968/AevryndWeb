"""Private attributed reference preview of ONE original complete hairstyle."""
from pathlib import Path
import bpy,numpy as np,time,importlib.util
from mathutils import Matrix
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('guide68inventory','inspect-female-next-r0068-guide-structure.py');base=module('guide68stage','inspect-female-next-r0065-eye-shading.py');R=m.R;E=m.E;S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend';SOURCE_SHA='4d0e3f67735ae68c5c1fa3c933f7cabb03cb547928e778f7067a8e699620b708'
def main():
    tick=time.time();assert m.sha(SRC)==SOURCE_SHA and m.sha(m.SRC)==m.SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC))
    for o in bpy.context.scene.objects:
        if o.type in ('MESH','CURVES'):o.hide_render=True
    with bpy.data.libraries.load(str(m.SRC),link=False) as (src,dst):dst.objects=['head','eyes','long hair main','long hair strands','long hair growth mesh']
    scale=.095;T=Matrix.Diagonal((scale,scale,scale,1.));T.translation=(0.,.015,1.562-16.410877227783203*scale);objects={o.name:o for o in dst.objects};controls=[]
    for name,o in objects.items():
        originalBasis=o.matrix_basis.copy();o.parent=None;bpy.context.scene.collection.objects.link(o);o.matrix_world=T@originalBasis if name=='eyes' else T;o.hide_render=name=='long hair growth mesh';o.hide_set(False)
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    for name in ('long hair main','long hair strands'):
        o=objects[name];d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;assert len(d.curves)<250000 and len(d.position_data)<15000000,(name,len(d.curves),len(d.position_data));P=np.empty(len(d.position_data)*3,dtype='f4');d.position_data.foreach_get('vector',P);assert np.isfinite(P).all();rad=d.attributes.get('radius');rr=np.empty(len(d.position_data),dtype='f4')
        if rad:rad.data.foreach_get('value',rr)
        controls.append({'name':name,'nativeGuides':len(o.data.curves),'evaluatedCurves':len(d.curves),'evaluatedPoints':len(d.position_data),'localRadiusRange': [float(rr.min()),float(rr.max())] if rad else None,'localBounds':[P.reshape(-1,3).min(0).tolist(),P.reshape(-1,3).max(0).tolist()]})
    m.save('original-style-evaluation.json',{'source':str(m.SRC),'sha256':m.SHA,'attribution':'Daniel Bystedt, Hair Styles Demo, CC BY-SA as declared in original text/publisher; original reference, not our own character.','referenceOnly':True,'notIntegratedOrPromoted':True,'uniformReferenceViewScale':scale,'worldMatrix':np.array(T).tolist(),'objects':controls,'secondsBeforeRender':time.time()-tick})
    base.shade.settings();base.k.b.camera('face');scene=bpy.context.scene;scene.camera.data.lens=85;scene.render.resolution_x=scene.render.resolution_y=640;scene.cycles.samples=16;scene.render.filepath=str(E/'reference-original-long-hair.png');bpy.ops.render.render(write_still=True);m.save('original-style-render-control.json',{'file':scene.render.filepath,'sourceSha256':m.SHA,'referenceOnly':True,'artist':'Daniel Bystedt','licenseNotice':'CC BY-SA (author did not specify version in file).','camera':np.array(scene.camera.matrix_world).tolist(),'settings':{'cyclesSamples':16,'resolution':640,'threads':4,'exposure':scene.view_settings.exposure},'seconds':time.time()-tick});print('R68_ORIGINAL_STYLE_REFERENCE',controls,time.time()-tick,flush=True)
if __name__=='__main__':main()
