"""One whole woman with the actual native artist Back1 particle construction.
No converted/cropped Bob cache, fitted scalp morph, independent root correction,
analytic strand field, shared ear tuck, density/width sweep or addon execution.
"""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util,datetime
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0122-native-swept-back-groom';D=R/'Reference/character/charmorph-vitruvian-cc0';SRC=S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend';OUT=S/'r0122-source/aevrynd-female-next-r0122-a-native-swept-back-groom.blend'
sp=importlib.util.spec_from_file_location('r122main',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
def native(o):
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());ps=ev.particle_systems['Back1'];md=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM' and m.particle_system.name=='Back1');settings=ps.settings;parents=len(ps.particles);children=len(ps.child_particles);N=2**settings.display_step+1;raw=np.empty((parents+children,N,3),'f4')
 for i in range(len(raw)):
  for j in range(N):raw[i,j]=ps.co_hair(ev,particle_no=i,step=j)
 counts=np.any(raw!=0,axis=2).sum(1);valid=np.arange(N)[None,:]<counts[:,None];assert np.isfinite(raw).all() and np.all(counts>=2) and np.all(raw[~valid]==0) and np.all(np.any(raw[valid]!=0,axis=1));gc=np.array([len(p.hair_keys) for p in ps.particles],'i4');guide=np.array([k.co_object(ev,md,p)[:] for p in ps.particles for k in p.hair_keys],'f4');starts=np.r_[0,np.cumsum(gc)[:-1]];A=np.array(o.matrix_world);error=float(np.linalg.norm((guide[starts]@A[:3,:3].T+A[:3,3])-raw[:parents,0],axis=1).max());assert error<2e-6
 return raw,counts.astype('i4'),guide,gc,{'parents':parents,'children':children,'pathCacheSlotsEach':N,'validSampleCount':int(counts.sum()),'validCountRange':[int(counts.min()),int(counts.max())],'allNativeParentRootsMatchCoObjectGuideRootsWorldMaxM':error,'useParentParticles':getattr(settings,'use_parent_particles',None),'nativeRendererNotReconstructedCacheCurves':True,'sourceDisplayAndRenderStepsEqual':settings.display_step==settings.render_step,'pathSamplesNotExactFiniteRenderSweptGeometry':True}
def main():
 tick=time.time();assert not OUT.exists();save('native-groom-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Directly reconnect inspected original Back1 native particle groom to the unchanged r117 complete woman; no shape-fit/density/width sweep.'});sourceHash=sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);before=a.protected();old=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];A=skin.matrix_world.copy();oldImages={im:im.filepath for im in bpy.data.images}
 with bpy.data.libraries.load(str(D/'hair.blend'),link=False) as (aa,bb):bb.objects=['hair-src']
 ob=bb.objects[0];bpy.context.scene.collection.objects.link(ob);ob.name='AFN122_ORIGINAL_NATIVE_BACK1_SCALP_AND_GROOM';ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False);ob.matrix_world=A;ob.show_instancer_for_render=False;ob.show_instancer_for_viewport=False
 for md in ob.modifiers:
  if md.type=='PARTICLE_SYSTEM':md.show_viewport=md.show_render=md.particle_system.name=='Back1'
 ps=ob.particle_systems['Back1'];ps.settings=ps.settings.copy();original={k:getattr(ps.settings,k) for k in ['child_type','child_percent','rendered_child_count','child_radius','child_roundness','clump_factor','clump_shape','use_clump_curve','roughness_1','roughness_2','root_radius','tip_radius','radius_scale','display_step','render_step','use_close_tip','shape']};reference=json.loads((E/'source-reference.json').read_text('utf-8'));assert original==reference['originalSettings'];ps.settings.child_percent=ps.settings.rendered_child_count;ob.data.materials.clear();ob.data.materials.append(bpy.data.materials['Brown hair']);ps.settings.material=1
 raw,counts,guide,gc,stats=native(ob);sourceVertices=q.arr(ob.data.vertices,'co',len(ob.data.vertices),3);default=np.load(D/'Default.npy');assert np.array_equal(sourceVertices,default.astype('f4'));assert a.protected()==before
 for im,path in oldImages.items():assert im.filepath==path
 old.hide_render=True;old.hide_set(True);ob['AFN122_source']='Original Vitruvian Back1 native particle/edit-path data, pinned CC0 source. Existing separate Brown material rights retained. No source script or addon.';ob['AFN122_scope']='Static whole-woman construction trial. Original particle widths/children/clump/roughness/paths, same existing source body matrix. Original source emitter hidden as instancer; actual skin remains r117. Not fitted to current native scalp, not accepted root attachment/contact/natural motion/runtime. No conversion to approximate cached Bob curves.'
 np.savez_compressed(E/'native-back-groom-lineage.npz',nativeRawWorldAPI=raw,validCacheCounts=counts,guideNative=guide,guideCounts=gc,emitterNative=sourceVertices,emitterMatrix=np.array(A))
 bpy.context.view_layer.update();b.deliver(0.);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert sha(SRC)==sourceHash
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sourceHash,'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'nativeGroomObject':ob.name,'sourceLibrary':str(D/'hair.blend'),'sourceLibrarySha256':sha(D/'hair.blend'),'sourceStyle':'Back1','sourceOriginalParticleSettings':original,'nativeCacheObservation':stats,'allOriginalEmitterVerticesExactlyMatchDefault':True,'sourceMatrixExactlySameAsInspectedOriginalReference':np.array_equal(np.array(A),np.array(reference['matrix'])),'allProtectedBodyKeysOldFibresAndRadiiBeforeHide':before,'allProtectedBodyKeysOldFibresAndRadiiVerifiedBeforeOnlyOldHairVisibilityChange':True,'originalBobDataRetainedHidden':old.name,'actualSkinSourceUnchanged':skin.name,'allOriginalImagePathsUnchanged':True,'newGroomConstructedWithoutAnyShapeMappingOrTuck':True,'naturalMovementFiniteContactCurrentScalpAttachmentAndRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ['face','body-face','profile','oblique','back']:
  rows.append(b.u.v.image('a-native-back-groom',view));save('a-view-controls.json',rows)
 print('R122_COMPLETE_NATIVE_BACK_GROOM_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
