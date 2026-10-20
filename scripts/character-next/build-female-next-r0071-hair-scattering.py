"""Restore the artist's actual Cycles hair branch on the complete r69 actor.

One material connection only: no pigment, roughness, radius or geometry tuning.
The existing EEVEE approximation remains available in the shared author group.
This does not implement hair dynamics or validate contacts/runtime.
"""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,sys,importlib.util
def module(n,p):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('scatter71rig','build-female-next-r0069-complete-controls.py')
R=m.R;S=m.S;E=R/'Evidence/character-female-next/r0071-hair-scattering'
SRC=S/'aevrynd-female-next-r0069-a-complete-controls-study.blend'
BOUNDED='--bounded-palette' in sys.argv
TAG='b' if BOUNDED else 'a'
OUT=S/('aevrynd-female-next-r0071-b-bounded-pigment-hair-study.blend' if BOUNDED else 'aevrynd-female-next-r0071-a-author-cycles-hair-study.blend')
SOURCE_SHA='f358d3c5a4d00ee6ad94d324612b33bdcf5aa4dde0bb19382d72bc7afabbb667'
HAIR=('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES')
def save(name,data): (E/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def open_source(p):
    bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);m.shade.settings();m.shade.g.E=E
def lights():
    return {o.name:{'matrix':np.array(o.matrix_world).tolist(),'energy':o.data.energy,'color':list(o.data.color)} for o in bpy.context.scene.objects if o.type=='LIGHT'}
def pilot(tag,view='face'):
    s=bpy.context.scene;m.shade.settings();m.k.b.camera(view);s.camera.data.lens=85
    s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/(tag+'-pilot-'+view+'.png'))
    controls={'camera':np.array(s.camera.matrix_world).tolist(),'lights':lights(),'samples':16,'resolution':640,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'frame':s.frame_current,'engine':s.render.engine,'hairPrimitive':s.render.hair_type}
    bpy.ops.render.render(write_still=True);save(tag+('-pilot-controls.json' if view=='face' else '-body-pilot-controls.json'),controls)
def main():
    tick=time.time()
    if '--failed-body-views' in sys.argv:
        for tag,p in [('baseline',SRC),('a',S/'aevrynd-female-next-r0071-a-author-cycles-hair-study.blend'),('b',S/'aevrynd-female-next-r0071-b-bounded-pigment-hair-study.blend')]:
            open_source(p);pilot(tag,'body-face')
        print('R71_REJECTED_FULL_BODY_VIEWS',time.time()-tick,flush=True);return
    if '--views' in sys.argv:
        for tag,p in [('baseline',SRC),('a',OUT)]:
            open_source(p);save(tag+'-full-view-controls.json',m.shade.render(tag,('face','body-face','oblique','profile','back','alternate-oblique')))
        print('R71_FULL_VIEWS_DONE',time.time()-tick,flush=True);return
    assert not OUT.exists() and sha(SRC)==SOURCE_SHA
    open_source(SRC);s=bpy.context.scene;source_lights=lights();old=bpy.data.materials['Brown hair'];mat=old.copy();mat.name='AFN71_BOUNDED_PIGMENT_CYCLES_HAIR' if BOUNDED else 'AFN71_AUTHOR_CYCLES_HAIR'
    group=mat.node_tree.nodes['Group'];route=mat.node_tree.nodes['Reroute.001'];link=next(l for l in mat.node_tree.links if l.to_node==route)
    assert link.from_node==group and link.from_socket.name=='EEVEE Shader'
    mat.node_tree.links.remove(link);mat.node_tree.links.new(group.outputs['Cycles Shader'],route.inputs[0])
    palette_change=None
    if BOUNDED:
        # The source full-random branch used a scalar as RGB, replacing the
        # palette with grey. Random now interpolates the two supplied colors.
        group.node_tree=group.node_tree.copy();group.node_tree.name='AFN71_AUTHOR_GROUP_BOUNDED_PIGMENT'
        t=group.node_tree;mix=t.nodes['Mix'];inp=t.nodes['Group Input'];oldlink=next(l for l in t.links if l.to_socket==mix.inputs[7])
        assert oldlink.from_node.bl_idname=='ShaderNodeHairInfo' and oldlink.from_socket.name=='Random'
        random=oldlink.from_socket;t.links.remove(oldlink)
        palette=t.nodes.new('ShaderNodeMixRGB');palette.name='AFN71_RANDOM_WITHIN_SUPPLIED_BROWN_PALETTE';palette.blend_type='MIX'
        t.links.new(random,palette.inputs[0]);t.links.new(inp.outputs['Color 1'],palette.inputs[1]);t.links.new(inp.outputs['Color 2'],palette.inputs[2]);t.links.new(palette.outputs['Color'],mix.inputs[7])
        palette_change={'old':'HairInfo Random scalar directly converted to grey RGB','new':'The same Random interpolates source Color 1 and Color 2; resulting RGB feeds the existing source color/root pipeline','sourceColor1':list(group.inputs['Color 1'].default_value),'sourceColor2':list(group.inputs['Color 2'].default_value),'noNewChosenPigmentOrRoughnessValues':True}
    assignments=[]
    for n in HAIR:
        o=bpy.data.objects[n]
        for i,v in enumerate(o.data.materials):
            if v==old:o.data.materials[i]=mat;assignments.append({'object':n,'slot':i})
    assert len(assignments)==2 and source_lights==lights()
    s['AFN71_scope']='Source Cycles Principled Hair branch. '+('Scalar random converted to interpolation within supplied brown palette. ' if BOUNDED else '')+'Hair geometry, native radii, source color endpoints, roughness, skin, light and rig untouched. No motion/contact/runtime acceptance.'
    bpy.context.preferences.filepaths.save_version=0;m.k.b.camera('face');s.camera.data.lens=85
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    save(TAG+'-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'change':{'material':mat.name,'group':group.node_tree.name,'oldOutput':'EEVEE Shader','newOutput':'Cycles Shader','allGroupParametersAndNodesUnchanged':not BOUNDED,'paletteCorrection':palette_change},'assignments':assignments,'renderer':'CYCLES','sourceShader':'Principled Hair BSDF.001 / CHIANG / COLOR','sourceCredit':'Daniel Bystedt. CC BY-SA license. Version unspecified by author/publisher. Derived groom/material study; body and rig data separately Vitruvian CC0.','newContactOrNaturalMotionOrRuntimeAcceptance':False,'secondsBeforePilot':time.time()-tick})
    pilot(TAG)
    if not BOUNDED:open_source(SRC);pilot('baseline')
    print('R71_PILOTS_DONE',TAG,time.time()-tick,flush=True)
if __name__=='__main__':main()
