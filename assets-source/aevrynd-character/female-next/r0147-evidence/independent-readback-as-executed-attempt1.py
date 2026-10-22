"""Minimum independent reopen/operation plus sampled aperture-ray falsification.
Known visible rejection precedes broad collision/gaze audits; no source is saved.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0147-outer-lid-surface'
def module(n,file):
 s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('r146minimum','build-female-next-r0146-connected-lining.py');a=h.a;sig=module('r146mats','build-female-next-r0131-native-hair-material.py')
def save(n,x):h.save(n,x)
def snap(names):return {n:a.geometry(bpy.data.objects[n]) for n in names}
def main():
 tick=time.time();b=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(b['output']);names=a.FIXED+a.MOVING;sn=h.c.h.SKIN;attachments=h.c.h.ATTACH
 assert a.a.sha(src)==b['sha256']
 bpy.ops.wm.open_mainfile(filepath=b['comparisonBaseline']);scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();baseline=snap(names);protected=a.a.protected();oldRaw={n:a.rawsig(bpy.data.objects[n]) for n in names if n!=sn};oldMats={m.name:sig.signature(m) for m in bpy.data.materials};oldGroups=[(g.name,g.lock_weight) for g in bpy.data.objects[sn].vertex_groups];oldWeights=h.vertex_weights(bpy.data.objects[sn])
 bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;rig=bpy.data.objects[b['actualRig']];skin=bpy.data.objects[sn];scene.frame_set(1);bpy.context.view_layer.update();base=snap(names)
 lineage=np.load(E.parent/'r0146-connected-palpebral-lining/connected-skin-lineage.npz');mapping=h.values(skin.data.attributes['AFN146_ORIGINAL_VERTEX_ID'].data,'value',len(skin.data.vertices),dtype='i4');ids=np.flatnonzero(mapping>=0);oldids=mapping[ids]
 assert np.array_equal(oldids,lineage['retainedOriginalSkinIds']) and len(np.unique(oldids))==len(oldids)==168906
 assert oldGroups==[(g.name,g.lock_weight) for g in skin.vertex_groups] and np.array_equal(h.vertex_weights(skin)[ids],oldWeights[oldids])
 assert a.a.protected()==protected and {n:a.rawsig(bpy.data.objects[n]) for n in oldRaw}==oldRaw and {m.name:sig.signature(m) for m in bpy.data.materials if m.name in oldMats}==oldMats
 neutral={n:float(np.linalg.norm(base[n][0][ids]-baseline[n][0][oldids],axis=1).max()) if n==sn else float(np.linalg.norm(base[n][0]-baseline[n][0],axis=1).max()) for n in names};assert max(neutral.values())<2e-6
 rows=[]
 for f in range(1,18):
  scene.frame_set(f);bpy.context.view_layer.update();now=snap(names);props={s:float(rig[p]) for s,p in h.PROPS.items()};assert all(np.isfinite(W).all() for W,T in now.values())
  for n in [sn]+attachments:
   ob=bpy.data.objects[n];assert ob.modifiers[0].type=='ARMATURE';keys=ob.data.shape_keys.key_blocks;assert len(keys)==17
   for side in ['L','R']:
    for k in range(1,9):assert abs(keys['AFN146_'+side+'_LAMELLAR_%02d'%k].value-max(0.,1-abs(props[side]*8-k)))<2e-6
  W,T=now[sn];areas=np.linalg.norm(np.cross(W[T[:,1]]-W[T[:,0]],W[T[:,2]]-W[T[:,0]]),axis=1);assert np.count_nonzero(areas==0)==0
  rows.append({'frame':f,'actualBlink':props,'skinExactZeroAreaTriangles':int(np.count_nonzero(areas==0)),'minimumTwiceAreaM2':float(areas.min()),'finite':True,'actual16NativeKeyValuesPerAffectedLayerMatch':True,'skinMaxMovementM':float(np.linalg.norm(W-base[sn][0],axis=1).max())})
 demo=rig.animation_data.action;slot=rig.animation_data.action_slot;rig.animation_data.action=None
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 for p in h.PROPS.values():rig[p]=0.
 rig.update_tag();bpy.context.view_layer.update();rest=snap(names);manual=[]
 for l,r in [(1.,0.),(0.,1.),(.5,.5),(1.,1.),(0.,0.)]:
  rig[h.PROPS['L']]=l;rig[h.PROPS['R']]=r;rig.update_tag();bpy.context.view_layer.update();now=snap(names);move={n:float(np.linalg.norm(now[n][0]-rest[n][0],axis=1).max()) for n in names};opposite=None
  if (l,r) in [(1.,0.),(0.,1.)]:
   mask=rest[sn][0][:,0]<-.002 if l else rest[sn][0][:,0]>.002;opposite=float(np.linalg.norm(now[sn][0][mask]-rest[sn][0][mask],axis=1).max());assert opposite<2e-6
  if l or r:assert move[sn]>.001
  else:assert max(move.values())<2e-6
  manual.append({'L':l,'R':r,'actualMovementM':move,'oppositeSideSkinMovementM':opposite})
 rig.animation_data.action=demo;rig.animation_data.action_slot=slot;scene.frame_set(1);rig.update_tag();bpy.context.view_layer.update();returned=snap(names);restore={n:float(np.linalg.norm(returned[n][0]-base[n][0],axis=1).max()) for n in names};assert max(restore.values())<2e-6 and a.a.protected()==protected
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath));assert p.is_file();textures.append({'relative':im.filepath,'absolute':str(p),'sha256':a.a.sha(p),'bytes':p.stat().st_size})
 save('minimum-independent-tarsal-corrective-readback.json',{'source':str(src),'sha256':b['sha256'],'independentlyReopened':True,'retainedOriginalOuterVertices':len(ids),'oldInteriorVerticesIntentionallyReplaced':1185,'retainedOriginalWeightsAndGroupDefinitionsExact':True,'otherOriginalRawMeshesAndOriginalMaterialGraphsExact':True,'hiddenRollbackExact':True,'neutralOriginalPointErrorsM':neutral,'all17ActualBlinkFrames':rows,'manualCurrentControls':manual,'actualNeutralAndControlStateRestored':True,'actualRestorationErrorsM':restore,'allReferencedExternalTextures':textures,'numericEvaluationBoundNotContactToleranceM':2e-6,'originalGaze49NotReverifiedAfterVisibleClosureRejection':True,'completeBlinkAppearanceContactOrRuntimeAccepted':False,'broadCollisionAuditNotRunAfterVisibleFailure':True,'seconds':time.time()-tick})
 # Sample exact mesh primary rays in the recorded face camera. This only diagnoses
 # raw Skin coverage at pixel centres; transparency/shading/render occupancy and
 # continuous/global closure/contact are explicitly not inferred.
 control=json.loads((E/'a-view-controls.json').read_text('utf-8'))[0];cam=scene.camera;cam.matrix_world=Matrix(control['camera']);cam.data.lens=control['lensMM'];scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;bpy.context.view_layer.update();corners=cam.data.view_frame(scene=scene);xs=[v.x for v in corners];ys=[v.y for v in corners];z=corners[0].z;origin=cam.matrix_world.translation;rot=cam.matrix_world.to_3x3();rays=[]
 for y in range(224,279):
  for x in range(212,430):
   local=Vector((min(xs)+(x+.5)/640*(max(xs)-min(xs)),max(ys)-(y+.5)/640*(max(ys)-min(ys)),z));rays.append((x,y,(rot@local).normalized()))
 rayRows=[];witness={}
 for f in [1,5,9,17]:
  scene.frame_set(f);bpy.context.view_layer.update();now=snap([sn]+a.MOVING);trees={n:BVHTree.FromPolygons([Vector(p) for p in W],T.tolist(),all_triangles=True) for n,(W,T) in now.items()};out=[]
  for x,y,d in rays:
   sh=trees[sn].ray_cast(origin,d);sd=float('inf') if sh[0] is None else sh[3]
   for n in a.MOVING:
    eh=trees[n].ray_cast(origin,d)
    if eh[0] is not None and eh[3]<sd:out.append([x,y,n,eh[2],float(eh[3]),None if sh[0] is None else float(sd)])
  witness[str(f)]=out;rayRows.append({'frame':f,'actualBlink':{s:float(rig[p]) for s,p in h.PROPS.items()},'sampledPixelCentreRays':len(rays),'eyeSurfaceHitBeforeActualFullSkinCount':len(out),'distinctPixelCentres':len(set((r[0],r[1]) for r in out))})
 save('sampled-aperture-skin-eye-ray-witnesses.json',{'sourceSha256':b['sha256'],'camera':control,'sampleRectanglePixels':[212,224,430,279],'poses':rayRows,'witnesses':witness,'rawActualMeshSkinVersusEyeSurfaceOnly':True,'notAllOccludersAlphaOrExactRenderedOccupancy':True,'notGlobalClosureDistanceFiniteThicknessSelfOrContinuousContact':True,'noPhysicalClearanceOrToleranceAdded':True})
 scene.frame_set(1);bpy.context.view_layer.update();assert all(np.array_equal(a.geometry(bpy.data.objects[n])[0],base[n][0]) for n in names);assert a.a.sha(src)==b['sha256']
 print('R147_MINIMUM_INDEPENDENT_NATIVE_CONTROL_RESTORE_AND_APERTURE_RAYS_DONE',rayRows,flush=True)
if __name__=='__main__':main()
