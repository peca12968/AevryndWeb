"""Minimum independent recovery and actual editing of source references only."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom';S=R/'engine/assets/characters/female-next/source/r0130-source'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arr(c,k,n,w=3):
 a=np.empty((n,w),'f4');c.foreach_get(k,a.ravel());return a
def main():
 tick=time.time();rows=[]
 p=S/'artist-original-ellie-restored-native-groom.blend';h=sha(p);bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['GEO-ellie_hair_cut.scalp'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());parts=[]
 for ps in o.particle_systems:
  md=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM' and m.particle_system.name==ps.name);ep=md.particle_system;proxy=bpy.data.objects[o.name+'-'+ps.name].evaluated_get(bpy.context.evaluated_depsgraph_get());P=arr(proxy.data.vertices,'co',len(proxy.data.vertices));actual=np.array([k.co_object(ev,md,ep.particles[i])[:] for i,pt in enumerate(ps.particles) for k in pt.hair_keys]);error=float(np.linalg.norm(actual-P[:len(actual)],axis=1).max());assert error<2e-5;parts.append({'name':ps.name,'parents':len(ps.particles),'restoredKeys':len(actual),'actualKeyAgainstSourceProxyMaxNativeUnits':error})
 assert sha(p)==h;rows.append({'source':str(p),'sha256':h,'bytes':p.stat().st_size,'reopened':True,'nativeGroomKeyDataRecovered':parts,'fullSourceRigWithoutHandlersNotQualified':True})
 p=S/'artist-original-ellie-native-curve-reference.blend';h=sha(p);bpy.ops.wm.open_mainfile(filepath=str(p));d=np.load(E/'original-native-studio-cache.npz');o=bpy.data.objects['AFN130_ORIGINAL_STUDIO_NATIVE_CACHE_CURVES'];bpy.context.view_layer.update()
 def read():
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());return arr(ev.data.position_data,'vector',len(ev.data.position_data))
 before=read();assert np.array_equal(before,d['world']);counts=np.array([c.points_length for c in o.data.curves]);assert np.array_equal(counts,d['counts']);r=arr(o.data.attributes['radius'].data,'value',len(before),1);index=int(counts[0]-1);raw=arr(o.data.position_data,'vector',len(before));edited=raw.copy();edited[index,1]+=.001;o.data.position_data.foreach_set('vector',edited.ravel());o.data.update_tag();bpy.context.view_layer.update();moved=read();delta=np.linalg.norm(moved-before,axis=1);assert .00099<float(delta.max())<.00101 and np.count_nonzero(delta>1e-6)==1
 o.data.position_data.foreach_set('vector',raw.ravel());o.data.update_tag();bpy.context.view_layer.update();assert np.array_equal(read(),before);assert np.array_equal(r,arr(o.data.attributes['radius'].data,'value',len(before),1));assert sha(p)==h
 rows.append({'source':str(p),'sha256':h,'bytes':p.stat().st_size,'reopened':True,'curves':len(counts),'points':len(before),'allSavedNativeCacheSamplesAndCountsExact':True,'actualDisplayedFreePointEditMaxSourceUnits':float(delta.max()),'pointsMovedAbove1um':int(np.count_nonzero(delta>1e-6)),'actualEditAndAllRadiiRestoredExactly':True,'scope':'Original source curve reference editing only, NOT current complete woman, guide-child coupling, root attachment, natural dynamics or contact/runtime acceptance.'})
 m=json.loads((R/'engine/assets/characters/female-next/female-next.asset.json').read_text('utf-8'));before=json.loads((E/'before.json').read_text('utf-8'));assert sha(R/'engine/assets/characters/female-next/female-next.asset.json')==before['priorManifestSha256'];assert sha(Path(m['workingCompleteWomanReference']['source']))==m['workingCompleteWomanReference']['sha256'];assert all(sha(R/k)==v for k,v in before['protectedUnrelatedHashes'].items())
 out={'sources':rows,'currentCompleteWomanAndManifestAndNineUnrelatedFilesUnchanged':True,'referenceOnlyNoCompleteCharacterOperationOrAppearanceGain':True,'naturalHairMotionFiniteContactAndRuntimeUnaccepted':True,'noNewModelScoreOrAcceptance':True,'seconds':time.time()-tick};(E/'minimum-reference-reopen-readback.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('R130_REFERENCE_ONLY_INDEPENDENT_REOPEN_EDIT_RESTORE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
