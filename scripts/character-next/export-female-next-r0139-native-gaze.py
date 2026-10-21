"""Portable baked development asset, not formal runtime promotion.
Original authoring file stays immutable; source-ID attributes exist only in memory.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
sp=importlib.util.spec_from_file_location('r139export','build-female-next-r0139-native-lid-follow.py' if False else Path(__file__).with_name('build-female-next-r0139-native-lid-follow.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;E=h.E
D=h.S.parent/'development/r0139';OUT=D/'aevrynd-female-next-r0139-gaze-development.glb';ATTRIBUTE='_AEVRYND_SOURCE_ID'
def main():
 tick=time.time();build=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(build['output']);assert a.a.sha(src)==build['sha256'];contact=json.loads((E/'actual-lid-ocular-surface-contact.json').read_text('utf-8'));assert not contact['relatedRawSurfaceFailureObserved'] and contact['allRequestedPoseObjectCasesCompleted'];seams=json.loads((E/'actual-attachment-seam-check.json').read_text('utf-8'));assert not seams['duplicateEdgeOpeningBeyondEvaluationBoundObserved'];assert not OUT.exists();D.mkdir(parents=True,exist_ok=True)
 h.save('development-export-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalRoundStartUTC':'2026-10-21T22:26:00+00:00','purpose':'One immutable source candidate, baked scene/skin joints into development GLB; not a new model candidate or formal engine/website promotion.','source':str(src),'sourceSHA256':build['sha256'],'storageBudgetAdditionalBytes':150000000,'numericReconstructionBoundM':2e-6,'boundIsExportNumericNotContactTolerance':True})
 bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;s.frame_set(1);s.frame_start=1;s.frame_end=49;s.render.fps=24;bpy.context.view_layer.update();names=[h.SKIN]+h.ATTACH+a.MOVING+h.STATIC;weights=np.load(E/'native-current-lid-skinning.npz');arrays={};refs={};motion={}
 for i,n in enumerate(names):
  ob=bpy.data.objects[n];assert not ob.hide_render;W,T=a.geometry(ob);assert len(W)==len(ob.data.vertices);prefix='m%d'%i
  if n==h.SKIN:ids=np.flatnonzero(weights['skinWeights'][:,1:].sum(1)>0)
  elif n in h.ATTACH:ids=np.flatnonzero(weights[n+'Weights'][:,1:].sum(1)>0)
  elif n in a.MOVING:ids=np.arange(len(W))
  else:ids=np.empty(0,dtype='i4')
  arrays[prefix+'_base']=W;arrays[prefix+'_triangles']=T;arrays[prefix+'_affected']=ids.astype('i4');motion[n]=[];refs[n]={'prefix':prefix,'nativeVertices':len(W),'nativeTriangles':len(T),'actualAffectedVertices':len(ids)}
 for f in range(1,50):
  s.frame_set(f);bpy.context.view_layer.update()
  for n in names:
   ids=arrays[refs[n]['prefix']+'_affected'];W,T=a.geometry(bpy.data.objects[n]);motion[n].append(W[ids])
 for n in names:arrays[refs[n]['prefix']+'_poses']=np.array(motion[n])
 np.savez_compressed(E/'development-native-pose-reference.npz',**arrays);h.save('development-native-pose-reference.json',{'source':str(src),'sourceSHA256':build['sha256'],'meshes':refs,'frames':list(range(1,50)),'fps':24,'GLTFTimeSeconds':'(nativeFrame-1)/24','coordinateReference':'Actual evaluated Blender world Z-up metres. GLB is glTF Y-up.','sourceVertexAttribute':ATTRIBUTE,'numericReconstructionBoundM':2e-6,'notRenderOrContactOrEnginePerformanceEvidence':True})
 s.frame_set(1);bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
 for n in names:
  ob=bpy.data.objects[n];ob.data=ob.data.copy();attr=ob.data.attributes.new(ATTRIBUTE,'FLOAT','POINT');attr.data.foreach_set('value',np.arange(len(ob.data.vertices),dtype='f4'));ob.hide_set(False);ob.select_set(True)
 rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];rig.hide_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig
 result=bpy.ops.export_scene.gltf(filepath=str(OUT),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='SCENE',export_bake_animation=True,export_frame_range=True,export_frame_step=1,export_force_sampling=True,export_sampling_interpolation_fallback='LINEAR',export_optimize_animation_size=False,export_anim_scene_split_object=False,export_nla_strips_merged_animation_name='AEVRYND_R139_NATIVE_GAZE',export_anim_slide_to_zero=True,export_def_bones=False,export_skins=True,export_apply=False,export_attributes=True,export_extras=True,export_cameras=False,export_lights=False,export_materials='EXPORT')
 assert result=={'FINISHED'} and OUT.is_file() and a.a.sha(src)==build['sha256'];h.save('development-export-summary.json',{'source':str(src),'sourceSHA256':build['sha256'],'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'selectedActualMeshes':names,'nativeRig':rig.name,'bakedFrameRange':[1,49],'fps':24,'bakedNativeLidDriversNoBlenderRuntimeDependencyIntended':True,'sourceIndexAttribute':ATTRIBUTE,'originalAuthoringFileUnmodified':True,'sourceGeometryAttributeChangesInMemoryOnly':True,'requiresIndependentGLBGeometryAnimationReadback':True,'formalRuntimeWebsiteOrEngineAcceptance':False,'sourceRights':'Angelica / DarkNik original NikZava284 CC-BY4.0 head/eye/hair/lash/wet/mouth and source skin; MakeHuman/Vitruvian CC0 body. Full inherited original attribution/legal/texture/modification history remains mandatory, not exclusive Aevrynd artwork.','seconds':time.time()-tick});print('R139_PORTABLE_NATIVE_GAZE_DEVELOPMENT_GLB_EXPORTED',OUT.stat().st_size,time.time()-tick,flush=True)
if __name__=='__main__':main()
