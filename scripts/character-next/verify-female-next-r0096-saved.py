"""Independent whole-source readback and cheap scoped contact falsification.
Not a rendered occupancy, all-body/self, continuous or natural motion proof.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0096-artist-bob-foundation'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
h=mod('r96ind','verify-female-next-r0090-rain-and-flow.py');p=mod('r96parity','verify-female-next-r0081-curly.py');m=h.m;q=h.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def main():
 tick=time.time();h.open_file(S/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend');names=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];sig={n:h.native.signature(bpy.data.objects[n]) for n in names};rig=h.rig_signature();lights=m.m.q.lights();mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)};face={n:q.hair(bpy.data.objects[n]).copy() for n in ['AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']};caps={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in ['AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID','AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE']};oldHair=h.helpers.hair_signature(bpy.data.objects['AFN94_SOURCE_WIDTH_RENDER_FIBRES']);body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);V,T=body['V'],body['T'];edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1);_,inc=np.unique(edges[:,0].astype('u8')*len(V)+edges[:,1],return_counts=True);closed=bool(np.all(inc==2));tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);skin=m.rig.k.mesh(bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING']);st=BVHTree.FromPolygons(skin['V'].tolist(),skin['T'].tolist(),all_triangles=True)
 ref=json.loads((E/'a-build-summary.json').read_text('utf8'));src=Path(ref['output']);assert sha(src)==ref['outputSha256'];h.open_file(src);assert sig=={n:h.native.signature(bpy.data.objects[n]) for n in names};assert rig==h.rig_signature() and lights==m.m.q.lights();assert mats=={n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert caps=={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in caps};assert oldHair==h.helpers.hair_signature(bpy.data.objects['AFN94_SOURCE_WIDTH_RENDER_FIBRES'])
 for n,x in face.items():assert np.array_equal(q.hair(bpy.data.objects[n]),x)
 actualBody=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);assert np.array_equal(actualBody['V'],V) and np.array_equal(actualBody['T'],T);z=np.load(E/'a-artist-Bob-lineage.npz');o=bpy.data.objects[ref['curveObject']];g=bpy.data.objects[ref['guideObject']];A=np.array(o.matrix_world);N=ref['pointsEach'];P=q.hair(o).reshape(-1,N,3);wanted=z['actualChildNative'].astype('f8')@A[:3,:3].T+A[:3,3];err=float(np.linalg.norm(P-wanted,axis=2).max());assert P.shape==(24800,N,3) and np.isfinite(P).all() and err<3e-6;d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;rad=q.arr(d.attributes['radius'].data,'value',P.size//3);assert np.array_equal(rad,z['radiusNative'].ravel());assert np.all(q.arr(d.attributes['curve_type'].data,'value',24800,dtype='i4')==0);G=q.arr(g.data.vertices,'co',len(g.data.vertices),3);guideError=float(np.linalg.norm(G-z['deformedGuideNative'],axis=1).max());assert guideError<1e-6 and len(g.data.vertices)==ref['originalAuthoredGuidePoints'] and len(z['guideCounts'])==248
 roots=P[:,0];rootDist=np.array([tree.find_nearest(Vector(pt))[3] for pt in roots]);sample=np.linspace(0,P.size//3-1,2048,dtype=int);witness=[];inspected=0;minimum=float('inf');radiusWorld=float(rad.max())*np.linalg.norm(A[:3,0])
 for index in sample:
  pt=P.reshape(-1,3)[index];co,no,faceID,dist=tree.find_nearest(Vector(pt));minimum=min(minimum,dist);inspected+=1
  if dist<=radiusWorld+1e-6:continue
  inside=[p.parity(tree,pt,direction) for direction in [(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)]]
  if closed and all(v is True for v in inside):
   sco,_,sf,sd=st.find_nearest(Vector(pt))
   if np.linalg.norm(np.array(sco)-np.array(co))<1e-6:witness.append({'curve':int(index//N),'point':int(index%N),'world':pt,'unsignedBodyDistanceM':dist,'unsignedVisibleSkinDistanceM':sd,'threeRayInside':inside})
   if len(witness)>=8:break
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file:
   path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.is_file();textures.append({'relative':im.filepath,'sha256':sha(path)})
 assert len(textures)==15 and not bpy.data.libraries
 result={'a':{'source':str(src),'sha256':sha(src),'status':'PASS_SAVED_ARTIST_DATA_ONLY_NO_COMPLETE_OPERATION','allUnrelatedBodyFaceRig52UVKeysWeightsDriversTeethBrowsLashesMaterialsLightsPreserved':True,'previousR94HairDataPreservedAsHiddenRollback':True,'actualChildRenderCurves':24800,'all248OriginalParentGuidesRetainedSeparately':True,'originalSourceRenderChildRolePolicyRetained':True,'pointsEach':N,'CatmullRomControlType0':True,'sourceCorrectRadiusAndCloseTipVerified':True,'savedControlMaximumWorldErrorM':err,'savedGuideMaximumNativeErrorM':guideError,'rootCentreUnsignedBodyDistanceQuantilesM':np.quantile(rootDist,[0,.5,.95,1]),'allRootCentreDistancesInspected':len(roots),'rootDistanceIsNotAnatomicalEmissionDomainOrFiniteRootAcceptance':True,'scopedStaticContact':{'bodyClosedTwoIncidentEdges':closed,'nativeControlKnotsPlanned':2048,'inspected':inspected,'strongAuthoringControlPointInteriorWitnesses':witness,'countsAreNotGlobalTotals':True,'minimumSampledUnsignedDistanceM':minimum,'globalSignedMinimumM':None,'actualCyclesOccupancyFiniteShaftSelfRootsCCDAndNaturalMovementCertified':False},'externalTextures':textures,'completeAppearanceOperationContactRuntimeAccepted':False,'seconds':time.time()-tick}}
 save('minimum-saved-readback.json',result);print('R96_INDEPENDENT_SAVED_DONE',err,guideError,len(witness),time.time()-tick,flush=True)
if __name__=='__main__':main()
