"""Cheap owned-source shader/geometry attribution, not a skin improvement.
Uniform reflectance keeps original geometry, roughness, normal, SSS and stage.
Base-color emission isolates pigment coordinate artifacts from light/shape.
"""
import bpy,importlib.util,json,time
from pathlib import Path
sp=importlib.util.spec_from_file_location('frame41skin',Path(__file__).with_name('build-female-next-r0041-root-frame-groom.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
ch=a.ch;f=ch.f;b=ch.b;v=ch.v;SRC=ch.rod.SRC
E=f.R/'Evidence/character-female-next/r0042-skin-continuity';E.mkdir(exist_ok=True)
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;body=bpy.data.objects[b.BODY];original=body.data.materials[0];before=f.state();f.E=E
    save('diagnostic-contract.json',{'source':str(SRC),'sha256':b.sha(SRC),'reason':'After two ineffective hair transfer rounds, stop that method family; inspect visible face/neck streaks on ONE owned complete character','hypothesis':'Pigment coordinate interpolation causes the large streaks, versus scan geometry/normal detail','held':['Actual complete geometry and hair','Original exposure/light/pose/color management','All optical/brow/lash materials','Skin normal,bump,roughness,SSS in uniform-reflectance diagnostic'],'smallTest':'Original beauty, original pigment emission and constant fallback reflectance beauty. No scoring/adoption from diagnostic.','resource':{'diagnosticMaxMinutes':10,'overallCheckpointUTC':'2026-10-19 14:10:07 UTC','blenderThreads':4,'heavyJobsAtOnce':1},'noGeometryOrAppearanceClaim':True})
    f.render('before');ch.review.extras('before',E)
    uniform=original.copy();uniform.name='AFN42_DIAG_UNIFORM_REFLECTANCE';nt=uniform.node_tree;shader=nt.nodes.get('Principled BSDF')
    for link in list(shader.inputs['Base Color'].links):nt.links.remove(link)
    shader.inputs['Base Color'].default_value=(.32,.23,.18,1);body.data.materials[0]=uniform;f.render('uniform-reflectance')
    emission=original.copy();emission.name='AFN42_DIAG_PIGMENT_ONLY';nt=emission.node_tree;shader=nt.nodes.get('Principled BSDF');color=shader.inputs['Base Color'].links[0].from_socket;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');emit=nt.nodes.new('ShaderNodeEmission');nt.links.new(color,emit.inputs['Color']);nt.links.new(emit.outputs[0],out.inputs['Surface']);body.data.materials[0]=emission;f.render('pigment-only')
    body.data.materials[0]=original;assert f.state()==before;save('diagnostic-integrity.json',{'source':str(SRC),'sha256':b.sha(SRC),'originalStateRestoredExact':True,'outputs':['before-face.png','before-oblique.png','before-profile.png','before-body-face.png','uniform-reflectance-face.png','uniform-reflectance-oblique.png','uniform-reflectance-profile.png','pigment-only-face.png','pigment-only-oblique.png','pigment-only-profile.png'],'seconds':time.time()-start})
    print('R42_DIAGNOSTIC_DONE',time.time()-start,flush=True)

if __name__=='__main__':main()
