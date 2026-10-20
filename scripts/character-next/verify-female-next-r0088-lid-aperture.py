"""Independent saved sculpt/lash response, reversal, endpoint and cheap crossings.
No intersection witness is not a clearance or continuous-contact certificate.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,sys
from mathutils.bvhtree import BVHTree
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0088-lid-aperture'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
k=mod('r88build','build-female-next-r0088-lid-aperture.py');m=k.m;q=m.q;v=mod('r88native','verify-female-next-r0076-crowns.py');cross=mod('r88cross','screen-female-next-r0074-oral-contact.py')
VARIANT='b' if '--variant-b' in sys.argv else 'a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):
 if VARIANT=='b' and n in ('minimum-source-readback.json','candidate-neutral-crossing-screen.json'):n='b-'+n
 (E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def controls(blink):
 o=bpy.data.objects['AFN59_FACE_CONTROLS'];o['blink_left']=o['blink_right']=blink;o.update_tag();bpy.context.view_layer.update()
def prepare(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1)
 for n in m.rig.native_names():
  for md in bpy.data.objects[n].modifiers:
   if md.type=='SUBSURF':md.levels=md.render_levels
 controls(0)
def snapshot():
 names=m.rig.native_names()[:4]+['AFN74_SKIN_AND_EXISTING_OCULAR_LINING','AFN59_LASHES_NATIVE_POINT_POSES'];return {n:q.geom(bpy.data.objects[n])[1].copy() for n in names}|{n:q.hair(bpy.data.objects[n]).copy() for n in ('AFN57_NATIVE_LASHES','AFN57_NATIVE_BROWS','AFN81_EDITABLE_CURLY_GUIDES')}
def errors(actual,wanted):
 out={n:float(np.linalg.norm(actual[n]-wanted[n],axis=1).max()) for n in wanted};assert max(out.values())<1e-6,out;return out
def screen(label):
 skin=bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'];rows=[]
 for n in m.rig.native_names()[:4]:
  V,T=cross.arrays(bpy.data.objects[n]);bounds=(V.min(0)-.002,V.max(0)+.002);P,F=cross.arrays(skin,bounds);a=BVHTree.FromPolygons(P.tolist(),F.tolist(),all_triangles=True,epsilon=0.);b=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.);pairs=a.overlap(b);witness=None;checked=0
  for i,j in pairs:
   checked+=1;point=cross.proper_cross(P[F[i]],V[T[j]])
   if point is not None:witness={'skinSubsetTriangle':int(i),'opticalTriangle':int(j),'worldPointM':point,'skinTriangleWorld':P[F[i]].tolist(),'opticalTriangleWorld':V[T[j]].tolist()};break
  rows.append({'opticalObject':n,'broadPhasePairs':len(pairs),'refinedPairsBeforeStop':checked,'firstStrongProperCrossing':witness,'skinSubsetAABBM':[x.tolist() for x in bounds]});print('R88_STRONG_CROSSING_SCREEN',label,n,len(pairs),bool(witness),flush=True)
  if witness is not None:break
 result={'status':'FALSIFIED_STRONG_SURFACE_CROSSING' if any(x['firstStrongProperCrossing'] is not None for x in rows) else 'NO_STRONG_CROSSING_FOUND_STILL_UNACCEPTED','pose':'neutral','pairs':rows,'scope':'Actual evaluated render-subdivision skin/lining versus original four optical surfaces, conservative2mm optical AABB subset; strict noncoplanar segment/triangle interior witnesses with0.1micrometre edge-interior margin.','globalSignedMinimumM':None,'coplanarSolidContainmentFiniteLashesThicknessSelfAndContinuousNotCertified':True};save(label+'-neutral-crossing-screen.json',result);return result
def main():
 tick=time.time();ref=json.loads((E/(VARIANT+'-build-summary.json')).read_text());src=Path(ref['source']);out=Path(ref['output']);assert sha(src)==ref['sourceSha256'] and sha(out)==ref['outputSha256'];line=np.load(E/(VARIANT+'-native-aperture-lineage.npz'));prepare(src);names=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];sig={n:v.signature(bpy.data.objects[n]) for n in names};neutral=snapshot();mats={a.name:m.rig.k.f.v.v32.material_signature(a) for a in bpy.data.materials if a.use_nodes};lights=m.m.q.lights();baseContact=screen('baseline');controls(1);closed=snapshot();prepare(out);enabled=bpy.data.objects[ref['control']];assert enabled['sculpt_enabled']==1.;current=snapshot();newResponse={n:{'maximumWorldMoveM':float(np.linalg.norm(current[n]-neutral[n],axis=1).max()),'changedPointsOver1Micrometre':int((np.linalg.norm(current[n]-neutral[n],axis=1)>1e-6).sum())} for n in neutral}
 for n in m.rig.native_names()[:4]+['AFN57_NATIVE_BROWS','AFN81_EDITABLE_CURLY_GUIDES']:assert np.array_equal(current[n],neutral[n]),n
 assert newResponse['AFN74_SKIN_AND_EXISTING_OCULAR_LINING']['maximumWorldMoveM']>1e-4 and newResponse['AFN57_NATIVE_LASHES']['maximumWorldMoveM']>1e-4;expectedHelper=line['sourceHelperNeutralWorld']+line['L_lashHelperWorldDelta']+line['R_lashHelperWorldDelta'];assert np.max(np.linalg.norm(current['AFN59_LASHES_NATIVE_POINT_POSES']-expectedHelper,axis=1))<1e-6;assert np.max(np.linalg.norm(current['AFN57_NATIVE_LASHES']-current['AFN59_LASHES_NATIVE_POINT_POSES'],axis=1))<1e-6;contact=screen('candidate');enabled['sculpt_enabled']=0.;enabled.update_tag();bpy.context.view_layer.update();reverse=errors(snapshot(),neutral);enabled['sculpt_enabled']=1.;enabled.update_tag();controls(1);endpoint=errors(snapshot(),closed);controls(0)
 for name in ('AFN60_BODY_ORAL_AND_OCULAR_LINING','AFN59_LASHES_NATIVE_POINT_POSES'):
  o=bpy.data.objects[name]
  for key in list(o.data.shape_keys.key_blocks):
   if key.name.startswith('AFN88_'):o.shape_key_remove(key)
 assert {n:v.signature(bpy.data.objects[n]) for n in names}==sig;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats;assert m.m.q.lights()==lights;textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file:
   p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.is_file();textures.append({'relative':im.filepath,'sha256':sha(p)})
 assert len(textures)==15 and not bpy.data.libraries and sha(out)==ref['outputSha256'];result={'status':'PASS_SAVED_NATIVE_SCULPT_LASH_RESPONSE_AND_ENDPOINT_REVERSAL_ONLY','source':str(out),'sha256':ref['outputSha256'],'actualNeutralResponse':newResponse,'actualLashPointsMatchDrivenHelper':True,'disablingSculptRecoversOriginalCompleteNeutralMaximumErrorsM':reverse,'newFadeAtClosedRecoversOriginalCompleteClosedMaximumErrorsM':endpoint,'originalNativeDataKeysUVWeightsDriversMaterialTreesAndLightsPreserved':True,'baselineContactStatus':baseContact['status'],'candidateContactStatus':contact['status'],'contactEvidence':['baseline-neutral-crossing-screen.json',('b-' if VARIANT=='b' else '')+'candidate-neutral-crossing-screen.json'],'externalTextures':textures,'savedSourceUnmodified':True,'intermediateBlinkLashFiniteSelfContinuousNaturalMotionRuntimeQualified':False,'seconds':time.time()-tick};save('minimum-source-readback.json',result);print('R88_SAVED_OPERATION_READBACK',contact['status'],time.time()-tick,flush=True)
if __name__=='__main__':main()
