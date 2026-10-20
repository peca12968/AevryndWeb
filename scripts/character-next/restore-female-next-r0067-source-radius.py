"""Repair a concrete native conversion omission, with a real particle control.

Blender's converted Curves have no radius attribute and default to 1cm.
Transfer the unchanged author diameters/close-tip rule, not a collision fit.
"""
from pathlib import Path
import bpy,numpy as np,time,importlib.util
sp=importlib.util.spec_from_file_location('eve67restorebuild',Path(__file__).with_name('build-female-next-r0067-native-eve.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
OUT=m.S/'aevrynd-female-next-r0067-b-source-radius-eve-study.blend'
def main():
    tick=time.time();a=m.read(m.E/'a-build-summary.json');assert m.m.sha(m.OUT)==a['outputSha256'] and not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(m.OUT));hair=bpy.data.objects[a['completeCurveObject']];emitter=bpy.data.objects['AFN67_ORIGINAL_FEMALE_EVE_EMITTER'];ps=emitter.particle_systems[0]
    assert not hair.data.attributes.get('radius');source=ps.settings;assert source.root_radius==source.tip_radius and source.shape==0. and source.child_size==1. and source.child_size_random==0.
    nominalRadius=float(source.root_radius*source.radius_scale*.5);assert 5.99e-5<nominalRadius<6.01e-5
    # Actual source PS render verifies the correct conversion visually. Hiding
    # the instancer mesh is supported separately from its particle paths.
    hair.hide_render=True;emitter.hide_render=False;emitter.hide_set(False);emitter.show_instancer_for_render=False;emitter.data.materials.clear();emitter.data.materials.append(hair.data.materials[0]);bpy.context.view_layer.update();m.m.save('native-source-preview-control.json',m.preview('native-source'))
    hair.hide_render=False;emitter.hide_render=True;emitter.hide_set(True);P,counts,oldR=m.curve_arrays(hair);ends=np.cumsum(counts)-1;radius=np.full(len(P),nominalRadius,dtype='f4')
    if source.use_close_tip:radius[ends]=0.
    hair.data.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',radius);bpy.context.view_layer.update();after,afterCounts,afterR=m.curve_arrays(hair);assert np.array_equal(P,after) and np.array_equal(counts,afterCounts) and np.array_equal(radius,afterR)
    hair['radiusTransfer']='Author root/tip diameter * radius_scale /2; original close-tip=0. Constant diameter/shape=0/child size1. No contact-driven radius or density change.'
    m.shade.settings();m.k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN67_status']='SOURCE_RADIUS_RESTORED_NATIVE_EVE_UNACCEPTED';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(m.E/'b-converted-eve-data.npz',positions=P,counts=counts,radii=radius,matrix=np.array(hair.matrix_world),starts=np.r_[0,np.cumsum(counts)[:-1]])
    s=float(np.linalg.norm(np.array(hair.matrix_world)[:3,:3],ord=2));m.m.save('b-build-summary.json',{'source':str(m.OUT),'sourceSha256':a['outputSha256'],'baselineSource':str(m.SRC),'baselineSha256':m.SOURCE_SHA,'output':str(OUT),'outputSha256':m.m.sha(OUT),'nativeConversionOmission':'No point radius attribute: default Curves radius1cm. Rejected technical intermediate A retained for history.','completeCurveObject':hair.name,'curves':len(counts),'points':len(P),'pointsPerCurve':sorted(set(counts.tolist())),'sourceRootDiameter':source.root_radius,'sourceTipDiameter':source.tip_radius,'sourceDiameterScale':source.radius_scale,'sourceCloseTip':source.use_close_tip,'explicitLocalRadiusM':nominalRadius,'worldShaftRadiusM':nominalRadius*s,'tipRadiusM':0. if source.use_close_tip else nominalRadius,'geometryAndCurveCountUnchangedFromA':True,'sameMaterialAsNativeParticleControl':hair.data.materials[0].name,'sourceHairThicknessOrDensityEdited':False,'newSoftwareAddonsOrEmbeddedCode':False,'secondsBeforeCorrectedPreview':time.time()-tick})
    m.m.save('b-preview-control.json',m.preview('b-eve'));print('R67_NATIVE_RADIUS_RESTORED',len(counts),nominalRadius,time.time()-tick,flush=True)
if __name__=='__main__':main()
