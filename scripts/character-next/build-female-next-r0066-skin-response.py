"""One source-grounded hypothesis: restore height units and skin transport.

Pigment/roughness maps, geometry and lighting are fixed. No source LUT,
procedural micro-noise or view-dependent source roughness group is copied.
This is a selected response study, not an exact original-material clone.
"""
from pathlib import Path
import bpy, json, time, sys, numpy as np, math
import importlib.util
sp=importlib.util.spec_from_file_location('skin66inspect',Path(__file__).with_name('inspect-female-next-r0066-skin-source.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
E=m.E;S=m.S;SRC=m.SRC;OUT=S/'aevrynd-female-next-r0066-a-source-skin-response-study.blend';shade=m.d.shade;k=m.d.k
def read(p):return json.loads(p.read_text(encoding='utf8'))
def record_preview(tag):
    s=bpy.context.scene;shade.settings();k.b.camera('face');s.camera.data.lens=85
    s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/(tag+'-preview-face.png'))
    camera=np.array(s.camera.matrix_world).tolist();bpy.ops.render.render(write_still=True)
    return {'file':s.render.filepath,'camera':camera,'resolution':640,'samples':16,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'lights':k.f.v.stage()['lights']}
def main():
    tick=time.time();shade.g.E=E
    if '--views' in sys.argv:
        ref=read(E/'a-build-summary.json');assert m.sha(OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));shade.settings();m.save('a-full-view-controls.json',shade.render('a-skin',('face','body-face','oblique','profile','alternate-oblique')));return
    if '--baseline-views' in sys.argv:
        assert m.sha(SRC)==m.SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));shade.settings();m.save('baseline-full-view-controls.json',shade.render('baseline-skin',('face','body-face','oblique','profile','alternate-oblique')));return
    assert not OUT.exists();assert m.sha(SRC)==m.SOURCE_SHA
    bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);stage=k.f.v.stage();m.save('baseline-preview-control.json',record_preview('baseline'))
    body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];scale=float(body.scale.x);assert max(abs(v-scale) for v in body.scale)<1e-7
    original=read(E/'source-material-diagnosis.json')['original']['groups']['VitruvianSkin'];sourceValues=read(E/'native-skin-values.json');natives={n['name']:n for n in original['nodes']};settings=sourceValues['sourceSettings']
    pvalues={i['socket']:i['value'] for i in natives['Principled BSDF']['inputs']}
    radius=[natives['Combine XYZ']['inputs'][i]['value'] for i in range(3)];factor=next(n['output'] for n in sourceValues['VitruvianSkin'] if n['name']=='Value.004');radius=[v*factor for v in radius]
    depth=float(natives['Math.002']['inputs'][1]['value'])*settings['Global Bump Strength']*scale
    transportScale=float(natives['Math.003']['inputs'][1]['value'])*settings['Subsurface Scale Multiplier']*scale
    assert sourceValues['sourceDisplacementMethod']=='BUMP' and settings['Age (Baby)']==settings['Age (Eldery)']==settings['Estrogen']==0.
    mat=bpy.data.materials['AFN57_CANONICAL_SKIN'].copy();mat.name='AFN66_SOURCE_HEIGHT_AND_SKIN_TRANSPORT';p=mat.node_tree.nodes['Principled BSDF'];bump=mat.node_tree.nodes['Bump'];changes=[]
    for name,value in [('Subsurface Weight',pvalues['Subsurface Weight']),('Subsurface Radius',radius),('Subsurface Scale',transportScale),('Subsurface Anisotropy',pvalues['Subsurface Anisotropy'])]:
        old=p.inputs[name].default_value;old=old if isinstance(old,(int,float)) else list(old);p.inputs[name].default_value=value;changes.append({'node':p.name,'input':name,'before':old,'after':value})
    oldMethod=p.subsurface_method;p.subsurface_method='RANDOM_WALK_SKIN';changes.append({'node':p.name,'property':'subsurface_method','before':oldMethod,'after':p.subsurface_method})
    for name,value in [('Strength',1.),('Distance',depth)]:
        old=bump.inputs[name].default_value;bump.inputs[name].default_value=value;changes.append({'node':bump.name,'input':name,'before':old,'after':value})
    assignments=[]
    for o in bpy.data.objects:
        if o.type!='MESH' or o.hide_render:continue
        for i,slot in enumerate(o.data.materials):
            if slot and slot.name=='AFN57_CANONICAL_SKIN':o.data.materials[i]=mat;assignments.append({'object':o.name,'slot':i})
    assert assignments and k.f.v.stage()==stage
    shade.settings();k.b.camera('face');bpy.context.scene['AFN66_status']='SOURCE_SKIN_RESPONSE_HYPOTHESIS_UNACCEPTED';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.save('a-build-summary.json',{'source':str(SRC),'sourceSha256':m.sha(SRC),'output':str(OUT),'outputSha256':m.sha(OUT),'changes':changes,'assignments':assignments,'uniformBodyScale':scale,'sourceHeightMultiplierM':depth,'sourceTransportScaleM':transportScale,'sourceSettings':settings,'pigmentRoughnessGeometryExposureFixed':True,'approximation':'Selected source height and skin-transport semantics only; no original microheight/LUT/view-dependent roughness/fauxcavity copied. Surface bump only, no geometry displacement or alpha change.','reference':'https://docs.blender.org/manual/en/5.0/render/shader_nodes/shader/principled.html','secondsBeforeCandidatePreview':time.time()-tick})
    m.save('a-preview-control.json',record_preview('a'));print('R66_SOURCE_SKIN_PREVIEW',time.time()-tick,flush=True)
if __name__=='__main__':main()
