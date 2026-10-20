"""One native artist-authored full Eve groom, converted without addon code.

Use the original canonical emitter and its supplied female morph. Preserve
the authored children/clump/thickness, bake native Curves, keep r65 anatomy.
"""
from pathlib import Path
import bpy,numpy as np,json,time,sys,importlib.util
def module(n,p):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('eve67diag','inspect-female-next-r0067-native-eve.py');base=module('eve67base','inspect-female-next-r0065-eye-shading.py');R=m.R;D=m.D;E=m.E;S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend';SOURCE_SHA='4d0e3f67735ae68c5c1fa3c933f7cabb03cb547928e778f7067a8e699620b708';OUT=S/'aevrynd-female-next-r0067-a-native-eve-study.blend';shade=base.shade;k=base.k
def read(p):return json.loads(p.read_text(encoding='utf8'))
def curve_arrays(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=np.empty(len(d.position_data)*3,dtype='f4');d.position_data.foreach_get('vector',P);counts=np.array([c.points_length for c in d.curves],dtype='i4');radius=np.empty(len(d.position_data),dtype='f4')
    a=d.attributes.get('radius')
    if a:a.data.foreach_get('value',radius)
    else:radius[:]=.01
    return P.reshape(-1,3),counts,radius
def preview(tag):
    s=bpy.context.scene;shade.settings();k.b.camera('face');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/(tag+'-preview-face.png'));camera=np.array(s.camera.matrix_world).tolist();bpy.ops.render.render(write_still=True)
    return {'file':s.render.filepath,'camera':camera,'resolution':640,'samples':16,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'lights':k.f.v.stage()['lights']}
def main():
    tick=time.time();shade.g.E=E
    if '--views' in sys.argv or '--b-views' in sys.argv:
        corrected='--b-views' in sys.argv;tag='b' if corrected else 'a';ref=read(E/(tag+'-build-summary.json'));path=Path(ref['output']);assert m.sha(path)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));shade.settings();m.save(tag+'-full-view-controls.json',shade.render(tag+'-eve',('face','body-face','oblique','profile','back','alternate-oblique')));return
    assert not OUT.exists() and m.sha(SRC)==SOURCE_SHA and m.sha(D/'hair.blend')==read(E/'native-eve-inspection.json')['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);stage=k.f.v.stage();body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];bodyMatrix=body.matrix_world.copy();originalHair=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'];hairMaterial=originalHair.data.materials[0]
    with bpy.data.libraries.load(str(D/'hair.blend'),link=False) as (src,dst):dst.objects=['hair-src']
    emitter=dst.objects[0];bpy.context.scene.collection.objects.link(emitter);bpy.ops.object.select_all(action='DESELECT');emitter.select_set(True);bpy.context.view_layer.objects.active=emitter
    if emitter.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    P=np.load(D/'Default.npy').astype('f4');actual=np.array([v.co[:] for v in emitter.data.vertices],dtype='f4');assert np.array_equal(actual,P) and emitter.data.shape_keys is None
    morph=np.load(D/'Gender_Female.npz');F=P.copy();F[morph['idx']]+=morph['delta'];r57=np.load(E.parent/'r0057-coherent-foundation/d-canonical-female-data.npz');assert np.array_equal(F,r57['female'].astype('f4'))
    # Keep only the actual Eve system; no other source hairstyles can evaluate.
    for i in range(len(emitter.particle_systems)-1,-1,-1):
        if emitter.particle_systems[i].name!='Eve':emitter.particle_systems.active_index=i;bpy.ops.object.particle_system_remove()
    assert len(emitter.particle_systems)==1;emitter.particle_systems.active_index=0;ps=emitter.particle_systems[0];settingsBefore=m.props(ps.settings);assert ps.name=='Eve' and ps.settings.child_percent==ps.settings.rendered_child_count==25
    if hasattr(ps.settings,'display_step'):ps.settings.display_step=ps.settings.render_step
    emitter.data.vertices.foreach_set('co',F.ravel());emitter.data.update();emitter.matrix_world=bodyMatrix
    for md in emitter.modifiers:
        if md.type=='PARTICLE_SYSTEM':md.show_viewport=md.show_render=True
    bpy.context.view_layer.update();ev=emitter.evaluated_get(bpy.context.evaluated_depsgraph_get());pse=ev.particle_systems[0];nativeCounts={'parents':len(pse.particles),'children':len(pse.child_particles),'settings':m.props(ps.settings)}
    before=set(bpy.data.objects);result=bpy.ops.curves.convert_from_particle_system();new=[o for o in bpy.data.objects if o not in before and o.type=='CURVES'];assert result=={'FINISHED'} and len(new)==1
    hair=new[0];hair.name='AFN67_NATIVE_EVE_COMPLETE_CURVES';hair.data.name='AFN67_NATIVE_EVE_AUTHOR_CURVES';hair.data.materials.clear();hair.data.materials.append(hairMaterial);hair.hide_render=False;hair.hide_set(False);P1,counts,radii=curve_arrays(hair);assert np.isfinite(P1).all() and np.isfinite(radii).all() and np.all(radii>0)
    emitter.name='AFN67_ORIGINAL_FEMALE_EVE_EMITTER';emitter.hide_render=True;emitter.hide_set(True);originalHair.hide_render=True;originalHair.hide_set(True)
    hair['scope']='Native author Eve full guide/children conversion on its exact canonical female emitter. Static study only; roots/body/self/continuous motion/runtime unaccepted.'
    emitter['scope']='Original native emitter with exact supplied female morph and r65 body matrix; hidden reference, not a second rendered body.'
    assert k.f.v.stage()==stage
    world=P1.astype('f8')@np.array(hair.matrix_world)[:3,:3].T+np.array(hair.matrix_world)[:3,3];scale=float(np.linalg.norm(np.array(hair.matrix_world)[:3,:3],ord=2));starts=np.r_[0,np.cumsum(counts)[:-1]]
    np.savez_compressed(E/'a-converted-eve-data.npz',positions=P1,counts=counts,radii=radii,matrix=np.array(hair.matrix_world),starts=starts)
    shade.settings();k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN67_status']='NATIVE_EVE_COMPLETE_STYLE_UNACCEPTED';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.save('a-build-summary.json',{'source':str(SRC),'sourceSha256':SOURCE_SHA,'originalGroom':read(E/'native-eve-inspection.json')['source'],'originalGroomSha256':read(E/'native-eve-inspection.json')['sha256'],'output':str(OUT),'outputSha256':m.sha(OUT),'nativeSystems':nativeCounts,'originalSettingsBeforeDisplayStepAlignment':settingsBefore,'nativeConversion':'bpy.ops.curves.convert_from_particle_system','completeCurveObject':hair.name,'curves':len(counts),'points':len(P1),'pointsPerCurve':sorted(set(counts.tolist())),'localRadiusRangeM':[float(radii.min()),float(radii.max())],'worldRadiusRangeM':[float(radii.min()*scale),float(radii.max()*scale)],'worldHairBounds':[world.min(0).tolist(),world.max(0).tolist()],'matrix':np.array(hair.matrix_world).tolist(),'curveModifiers':[{'name':md.name,'type':md.type} for md in hair.modifiers],'originalHairHidden':True,'bodyMorphMatchesR57CanonicalFemaleExactly':True,'noCrossBodyFitOrRootClamp':True,'sameMaterialAsR65Hair':hairMaterial.name,'sourceDiameterDescriptions':read(E/'native-eve-inspection.json')['radiusDescriptions'],'sourceThicknessOrDensityEdited':False,'secondsBeforePreview':time.time()-tick})
    m.save('a-preview-control.json',preview('a-eve'));print('R67_NATIVE_EVE_FIRST_PREVIEW',len(counts),len(P1),time.time()-tick,flush=True)
if __name__=='__main__':main()
