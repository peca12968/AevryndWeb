"""Minimum independent recovery of three native-groom/card construction states.
No broad motion/contact audit after visible failures. No complete operation claim.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('r122minimum',Path(__file__).with_name('build-female-next-r0122-native-back-groom.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;E=a.E;S=a.S
def main():
 tick=time.time();buildA=json.loads((E/'a-build-summary.json').read_text('utf-8'));checks={};originalTextures=json.loads((E.parent/'r0117-native-fibre-brows/minimum-saved-native-brow-readback.json').read_text('utf-8'))['allReferencedExternalTextures'];originalNames={row['name'] for row in originalTextures}
 for label in ['a','b','c']:
  info=json.loads((E/(label+'-build-summary.json')).read_text('utf-8'));path=Path(info['output']);digest=a.sha(path);bpy.ops.wm.open_mainfile(filepath=str(path));b.deliver(0.);old=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];assert old.hide_render and old.hide_get();old.hide_set(False);bpy.context.view_layer.update();protected=a.a.protected();assert protected==buildA['allProtectedBodyKeysOldFibresAndRadiiBeforeHide'];old.hide_set(True);bpy.context.view_layer.update();textures=[]
  for name in originalNames:
   image=bpy.data.images[name];p=Path(bpy.path.abspath(image.filepath));assert p.is_file(),str(p);row=next(t for t in originalTextures if t['name']==name);assert a.sha(p)==row['sha256'];textures.append({'name':name,'relative':image.filepath,'absolute':str(p),'bytes':p.stat().st_size,'sha256':row['sha256']})
  row={'candidate':{'source':str(path),'sha256':digest,'bytes':path.stat().st_size},'allOriginalCompleteSkinKeysOldFibreDataRadiiAndActualNeutralGeometryExact':True,'originalBobRetainedHidden':True,'allOriginal17TexturesExact':True,'allReferencedExternalTextures':textures,'completeOperationAccepted':False,'fullNaturalMotionFiniteContactAndRuntimeUnaccepted':True}
  if label in ['a','b']:
   hair=bpy.data.objects['AFN122_ORIGINAL_NATIVE_BACK1_SCALP_AND_GROOM'];line=np.load(E/('native-back-groom-lineage.npz' if label=='a' else 'b-cranial-alignment-lineage.npz'));raw,counts,guide,gc,stats=a.native(hair);assert np.array_equal(counts,line['validCacheCounts']) and np.array_equal(guide,line['guideNative']) and np.array_equal(gc,line['guideCounts']);err=float(np.linalg.norm(raw-line['nativeRawWorldAPI' if label=='a' else 'nativeRawWorldAPI'],axis=2).max());assert err<2e-6
   # All1044 parent roots, closest Euclidean surface distance and local normal
   # side only. Neither distance nor normal sign is a global inside certificate.
   d,W,T=b.u.b.geom(bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD']);tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True);dist=[];local=[]
   for p in raw[:stats['parents'],0]:
    hit,no,fi,dd=tree.find_nearest(Vector(p));dist.append(dd);local.append(float((p-np.array(hit))@np.array(no)))
   row.update({'nativeCacheObservation':stats,'originalNativeGuidesAndCacheCountsExactlyRecovered':True,'actualReopenedPathSampleWorldMaximumErrorM':err,'all1044ParentRootSampleNearestSurfaceDistancesM':{'quantiles':np.quantile(dist,[0,.5,.95,1]),'localNearestNormalProjectionQuantiles':np.quantile(local,[0,.5,.95,1]),'representation':'Actual evaluated native parent path-cache root points only; all1044 included. Not all render children, finite radius, swept native interpolation, signed global distances/inside classification or continuous contact proof.','rootSurfaceAttachmentNotQualified':True},'allOriginalParticleSettingsSameAsRecorded':all(getattr(hair.particle_systems['Back1'].settings,k)==v for k,v in buildA['sourceOriginalParticleSettings'].items())})
  else:
   hair=bpy.data.objects['AFN122_ORIGINAL_NATIVE_BOB_ALPHA_CARDS'];line=np.load(E/'c-native-card-lineage.npz');d,W,T=b.u.b.geom(hair);assert np.array_equal(W,line['evaluatedNominalShellWorld']) and np.array_equal(T,line['evaluatedNominalShellTriangles']);uv=q.arr(hair.data.uv_layers['NativeBobUV'].data,'uv',len(hair.data.loops),2);assert np.array_equal(uv,line['originalUV']);image=next(n.image for n in hair.data.materials[0].node_tree.nodes if n.bl_idname=='ShaderNodeTexImage');p=Path(bpy.path.abspath(image.filepath));assert p.is_file() and a.sha(p)==info['texture']['sha256'];row['allReferencedExternalTextures'].append({'name':image.name,'relative':image.filepath,'absolute':str(p),'bytes':p.stat().st_size,'sha256':a.sha(p)})
   # Actual original card vertex edit propagates to displayed nominal shell.
   point=0;co=q.arr(hair.data.vertices,'co',len(hair.data.vertices),3);edit=co.copy();edit[point,0]+=.0002;hair.data.vertices.foreach_set('co',edit.ravel());hair.data.update();bpy.context.view_layer.update();ed,EW,ET=b.u.b.geom(hair);delta=float(np.linalg.norm(EW-W,axis=1).max());assert delta>0;hair.data.vertices.foreach_set('co',co.ravel());hair.data.update();bpy.context.view_layer.update();rd,RW,RT=b.u.b.geom(hair);restore=float(np.linalg.norm(RW-W,axis=1).max());assert restore==0
   row.update({'originalCardsUVAndEvaluatedNominalShellExactlyRecovered':True,'originalFullRGBATextureExact':True,'nominalThicknessM':hair.modifiers['AFN122_NOMINAL_CARD_THICKNESS_0P1MM'].thickness,'actualUnsavedCardEditDisplayedMaxMovementM':delta,'actualCardEditRestoreMaxErrorM':restore,'rawCardEnvelopeNotExactAlphaOccupiedHairVolume':True})
  assert a.sha(path)==digest==info['sha256'];checks[label]=row
 a.save('minimum-saved-groom-readback.json',{'status':'THREE_COMPLETE_NATIVE_CONSTRUCTION_STATES_INDEPENDENTLY_REOPENED_MINIMUM_SCOPE','sources':checks,'noBroadMotionOrContactAuditAfterVisibleFailure':True,'noSourceOverwrittenDuringReadback':True,'seconds':time.time()-tick});print('R122_MINIMUM_THREE_SOURCE_READBACK_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
