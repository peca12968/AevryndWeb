"""Independent saved-woman data/semantic-width checks; no broad failed-groom audit."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0094-authored-growth-routing';S=R/'engine/assets/characters/female-next/source'
def mod(n,p):
 sp=importlib.util.spec_from_file_location(n,p);a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
h=mod('r94independent',Path(__file__).with_name('verify-female-next-r0090-rain-and-flow.py'));parity=mod('r94parity',Path(__file__).with_name('verify-female-next-r0081-curly.py'));policy=mod('r94widthpolicy',R/'engine/character/groom_import_semantics.py');m=h.m;q=h.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def main():
 tick=time.time();h.open_file(S/'aevrynd-female-next-r0092-a-native-Eve-groom.blend');names=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];sig={n:h.native.signature(bpy.data.objects[n]) for n in names};rig=h.rig_signature();lights=m.m.q.lights();mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)};faces={n:q.hair(bpy.data.objects[n]).copy() for n in ['AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']};caps={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in ['AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID','AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE']};results={};proof=json.loads((E/'radius-semantics-proof.json').read_text('utf8'));sourceSettings=json.loads((E/'original-Eve-emission.json').read_text('utf8'))['settings'];bExpected=np.array(policy.legacy_particle_point_radii(sourceSettings,33),'f4')
 refs=[(tag,json.loads((E/(tag+'-build-summary.json')).read_text('utf8'))) for tag in ['a','b','c']];refs.append(('c-visible',json.loads((E/'c-visibility-repair.json').read_text('utf8'))))
 for tag,ref in refs:
  src=Path(ref['output']);assert sha(src)==ref['outputSha256'];h.open_file(src);assert sig=={n:h.native.signature(bpy.data.objects[n]) for n in names};assert rig==h.rig_signature() and lights==m.m.q.lights();assert mats=={n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert caps=={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in caps}
  for n,V in faces.items():assert np.array_equal(q.hair(bpy.data.objects[n]),V)
  row={'source':str(src),'sha256':sha(src),'unrelatedBodyFaceNativeCagesKeysUVWeightsDriversRig52TeethBrowsLashesMaterialsLightsPreserved':True,'status':'REOPEN_DATA_ONLY_NO_NEW_COMPLETE_OPERATION','completeAppearanceContactNaturalMotionRuntimeAccepted':False}
  if tag in ['a','b']:
   a=np.load(E/'a-growth-volume-lineage.npz');name=ref['curveObject'];o=bpy.data.objects[name];P=q.hair(o).reshape(-1,33,3);z=a if tag=='a' else np.load(E/'b-source-width-lineage.npz');expected=z['actualWorld'];err=float(np.linalg.norm(P-expected,axis=2).max());assert err<2e-6 and P.shape==(28002,33,3) and np.isfinite(P).all();d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;rad=q.arr(d.attributes['radius'].data,'value',P.size//3).reshape(-1,33);assert len(d.curves)==28002 and all(c.points_length==33 for c in d.curves)
   if tag=='b':assert np.array_equal(rad,np.broadcast_to(bExpected,rad.shape))
   else:assert np.max(abs(rad-float(proof['sourceRootDiameterNativeM'])))<1e-10
   body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);V,T=body['V'],body['T'];ids=a['rootBodyTriangle'];tri=V[T[ids]];bary=a['rootBarycentric'];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None];scale=np.linalg.norm(np.array(o.matrix_world)[:3,0]);root=np.einsum('ni,nij->nj',bary,tri)+normal*rad[:,0,None]*scale;re=float(np.linalg.norm(P[:,0]-root,axis=1).max());assert bary.min()>=0 and np.max(abs(bary.sum(1)-1))<1e-12 and re<2e-6;assert np.all(np.isin(body['nativeTriangleFace'][ids],a['allowedNativeFaces']))
   row.update(actualCurves=28002,pointsEach=33,allSourceStrandsRootIDsRetained=True,maximumSavedWorldErrorM=err,rootSemanticTriangleBarycentricMaximumErrorM=re,rootBarycentricMinimum=float(bary.min()),rootDomainIsSourceAuthorScalpNativeFaces=True,domainIsNotAnatomicalFollicleProof=True,correctSourceNativeRadiusPolicyMatches=(tag=='b'),worldRootRadiusM=float(rad[0,0])*scale)
   if tag=='b':
    tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);skin=m.rig.k.mesh(bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING']);st=BVHTree.FromPolygons(skin['V'].tolist(),skin['T'].tolist(),all_triangles=True);edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1);_,inc=np.unique(edges[:,0].astype('u8')*len(V)+edges[:,1],return_counts=True);closed=bool(np.all(inc==2));pts=np.concatenate((P[:,1:].reshape(-1,3),((P[:,:-1]+P[:,1:])*.5).reshape(-1,3)));ix=np.linspace(0,len(pts)-1,8192,dtype=int);witness=[];inspected=0;minimum=float('inf')
    for index in ix:
     pt=pts[index];co,no,ti,dist=tree.find_nearest(Vector(pt));minimum=min(minimum,dist);inspected+=1
     if dist<=rad.max()*scale+1e-6:continue
     inside=[parity.parity(tree,pt,d) for d in [(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)]]
     if closed and all(v is True for v in inside):
      sco,_,sf,sd=st.find_nearest(Vector(pt))
      if np.linalg.norm(np.array(co)-np.array(sco))<1e-6:witness.append({'sampleIndex':int(index),'world':pt,'unsignedBodyDistanceM':dist,'unsignedVisibleSkinDistanceM':sd,'threeRayInside':inside,'pointType':'knot' if index<P[:,1:].size//3 else 'midpoint'})
      if len(witness)>=8:break
    row['scopedStaticContact']={'bodyClosedTwoIncidentEdges':closed,'sampledKnotsMidpointsPlanned':8192,'sampledInspected':inspected,'strongInteriorWitnesses':witness,'minimumSampledUnsignedDistanceM':minimum,'globalSignedMinimumM':None,'countsAreNotGlobalTotals':True,'finiteShaftSelfRootsActualCyclesCCDOrNaturalMotionAccepted':False}
  else:
   o=bpy.data.objects['AFN94_NATIVE_EVE_EMITTER_AND_EDITABLE_GUIDES'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());ps=ev.particle_systems['Eve'];z=np.load(E/'c-native-emitter-lineage.npz');actual=q.arr(o.data.vertices,'co',len(o.data.vertices),3);assert len(actual)==37436 and np.max(abs(actual-z['targetBodyNative']))<1e-7;assert len(ps.particles)==1077 and len(ps.child_particles)==26925;settings={k:getattr(ps.settings,k) for k in sourceSettings if hasattr(ps.settings,k) and k in ['root_radius','tip_radius','radius_scale','use_close_tip','shape','render_step','child_roundness','clump_factor']}
   for k,value in settings.items():assert value==sourceSettings[k],k
   row.update(nativeEditedGuides=1077,sourceRenderChildren=26925,nativeGuideHairKeys=sum(len(p.hair_keys) for p in ps.particles),nativeSourceSettingsPreserved=True,sourceNativeMorphCorrespondencesVerified=True,emitterHideRender=o.hide_render,nativeRootFollowingNotNaturalDynamicsOrContactProof=True)
  textures=[]
  for image in bpy.data.images:
   if image.source=='FILE' and not image.packed_file:
    path=Path(bpy.path.abspath(image.filepath));assert image.filepath.startswith('//') and path.is_file();textures.append({'relative':image.filepath,'sha256':sha(path)})
  assert len(textures)==15 and not bpy.data.libraries;row['externalTextures']=textures;results[tag]=row;save('minimum-saved-readback.json',results);print('R94_INDEPENDENT',tag,time.time()-tick,flush=True)
 print('R94_READBACK_DONE',flush=True)
if __name__=='__main__':main()
