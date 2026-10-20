"""Independent saved complete-woman readback and cheap authoring-path witnesses.
Rejected static pilots do not receive full animation/self/CCD/runtime audits.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0093-surface-bound-direct-rods';S=R/'engine/assets/characters/female-next/source'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
h=mod('r93independent','verify-female-next-r0090-rain-and-flow.py');p=mod('r93parity','verify-female-next-r0081-curly.py');m=h.m;q=h.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def main():
 tick=time.time();src=S/'aevrynd-female-next-r0092-a-native-Eve-groom.blend';h.open_file(src);names=m.rig.native_names()+['AFN59_LASHES_NATIVE_POINT_POSES'];sig={n:h.native.signature(bpy.data.objects[n]) for n in names};rig=h.rig_signature();mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)};lights=m.m.q.lights();face={n:q.hair(bpy.data.objects[n]).copy() for n in ['AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES']};old=h.helpers.hair_signature(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES']);caps={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in ['AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID','AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE']};rows={}
 for tag in ['a','b']:
  file=E/(tag+'-build-summary.json')
  if not file.exists():continue
  ref=json.loads(file.read_text('utf8'));out=Path(ref['output']);assert sha(out)==ref['outputSha256'];h.open_file(out)
  assert sig=={n:h.native.signature(bpy.data.objects[n]) for n in names};assert rig==h.rig_signature();assert lights==m.m.q.lights();assert mats=={n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert caps=={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in caps};assert old==h.helpers.hair_signature(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'])
  for n,V in face.items():assert np.array_equal(q.hair(bpy.data.objects[n]),V)
  z=np.load(E/(tag+'-binding-and-chain-lineage.npz'));o=bpy.data.objects['AFN93_SURFACE_BOUND_RENDER_FIBRES'];P=q.hair(o).reshape(-1,33,3);expected=z['actualWorld'];error=float(np.linalg.norm(P-expected,axis=2).max());assert error<2e-6 and len(P)==28002 and np.isfinite(P).all();d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;assert len(d.curves)==28002 and all(c.points_length==33 for c in d.curves);radius=q.arr(d.attributes['radius'].data,'value',P.size//3).reshape(-1,33)*np.linalg.norm(np.array(o.matrix_world)[:3,0]);assert np.max(abs(radius-z['worldRadius']))<1e-10
  body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);V,T=body['V'],body['T'];assert np.array_equal(T,z['bodyT']) and np.max(abs(V-z['bodyV']))<1e-7;tri=V[T[z['rootTriangle']]];bary=z['rootBarycentric'];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None];root=np.einsum('ni,nij->nj',bary,tri)+normal*radius[:,0,None];rootError=float(np.linalg.norm(P[:,0]-root,axis=1).max());assert np.max(abs(bary.sum(1)-1))<1e-8 and rootError<2e-6;outsideBary=int(np.count_nonzero(np.any(bary < -1e-7,axis=1)))
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file:
    path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.is_file();textures.append({'relative':im.filepath,'sha256':sha(path)})
  assert len(textures)==15 and not bpy.data.libraries
  edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1);_,inc=np.unique(edges[:,0].astype('u8')*len(V)+edges[:,1],return_counts=True);closed=bool(np.all(inc==2));tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);skin=m.rig.k.mesh(bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING']);st=BVHTree.FromPolygons(skin['V'].tolist(),skin['T'].tolist(),all_triangles=True)
  # Both knots and inter-knot midpoints. This is still a sample, not a
  # swept capsule or exact Cycles primitive occupancy verification.
  pts=np.concatenate((P[:,1:].reshape(-1,3),((P[:,:-1]+P[:,1:])*.5).reshape(-1,3)));sample=np.linspace(0,len(pts)-1,8192,dtype=int);witness=[];near=0;minimum=float('inf');checked=0
  for idx in sample:
   point=pts[idx];co,no,f,dist=tree.find_nearest(Vector(point));minimum=min(minimum,dist);checked+=1
   if dist<=radius.max()+1e-6:near+=1;continue
   inside=[p.parity(tree,point,direction) for direction in [(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)]]
   if closed and all(i is True for i in inside):
    sco,_,sf,sd=st.find_nearest(Vector(point));agreement=float(np.linalg.norm(np.array(sco)-np.array(co)))
    if agreement<1e-6:witness.append({'sampleIndex':int(idx),'world':point,'unsignedBodyDistanceM':dist,'unsignedVisibleSkinDistanceM':sd,'threeRayInside':inside,'pointType':'knot' if idx<P[:,1:].size//3 else 'midpoint'})
    if len(witness)>=8:break
  rows[tag]={'source':str(out),'sha256':sha(out),'status':'REOPEN_FINITE_DATA_ONLY_BARYCENTRIC_DOMAIN_UNQUALIFIED','actualCurves':28002,'pointsEach':33,'allSourceStrandsAndRadiiRetained':True,'savedMaximumWorldErrorM':error,'all28002RootsActualTriangleBarycentricRadiusExitMaximumErrorM':rootError,'rootBindingIsNotAnatomicalFollicleOrLiveMotionProof':True,'rootBarycentricMinimum':float(bary.min()),'rootsOutsideOriginalStrictBarycentricDomain':outsideBary,'originalDomainGuardNotPassedAndNotRelaxedForAcceptance':True,'allUnrelatedNativeBodyFaceCagesKeysUVWeightsDriversRig52TeethBrowsLashesMaterialsLightsPreserved':True,'externalTextures':textures,'bodyClosedTwoIncidentEdges':closed,'sampledKnotsAndMidpointsPlanned':8192,'sampledInspected':checked,'nearSurfaceSamplesNotCertifiedContactOrPenetration':near,'minimumSampledUnsignedDistanceM':minimum,'strongInteriorWitnesses':witness,'globalSignedMinimumM':None,'globalBodySelfRootsFiniteShaftCCDActualCyclesNaturalMotionRuntimeAccepted':False,'maximumDisplayedEdgeStrainFromSolver':ref['rows'][-1]['maximumRelativeEdgeStrain'],'seconds':time.time()-tick};save('minimum-saved-readback.json',rows);print('R93_INDEPENDENT',tag,error,rootError,len(witness),time.time()-tick,flush=True)
 print('R93_INDEPENDENT_DONE',flush=True)
if __name__=='__main__':main()
