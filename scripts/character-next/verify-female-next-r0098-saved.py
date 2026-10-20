"""Minimum independent reopen after visible structural rejection.
No animation expansion or old-head proxy contact certificate for the new head.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0098-whole-head-foundation'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
h=mod('r98saved','verify-female-next-r0090-rain-and-flow.py');m=h.m;q=h.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def evaluated(o):
 d,V=q.geom(o);d.calc_loop_triangles();return V,q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4')
def main():
 tick=time.time();h.open_file(S/'aevrynd-female-next-r0097-neutral-scalp-control-reference.blend')
 names=m.rig.native_names();sig={n:h.native.signature(bpy.data.objects[n]) for n in names};rig=h.rig_signature();lights=m.m.q.lights();mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes and (x.users or x.use_fake_user)}
 teeth={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in ['AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID']};toothWorld={n:h.world(bpy.data.objects[n]).copy() for n in teeth}
 hairName='AFN97_TUCKED_ARTIST_BOB_CHILDREN';oldHair=q.hair(bpy.data.objects[hairName]).reshape(24800,17,3).copy();oldRadius=q.arr(bpy.data.objects[hairName].data.attributes['radius'].data,'value',24800*17).copy();result={}
 for tag in ['a','b']:
  ref=json.loads((E/(tag+'-build-summary.json')).read_text('utf8'));path=Path(ref['output']);assert sha(path)==ref['outputSha256'];h.open_file(path)
  assert rig==h.rig_signature() and lights==m.m.q.lights()
  assert mats=={n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}
  assert all(sig[n]==h.native.signature(bpy.data.objects[n]) for n in names if n!='AFN60_BODY_ORAL_AND_OCULAR_LINING')
  unchangedBody=sig['AFN60_BODY_ORAL_AND_OCULAR_LINING']==h.native.signature(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'])
  if tag=='b':assert unchangedBody and teeth=={n:h.helpers.cap_signature(bpy.data.objects[n]) for n in teeth}
  toothD={n:float(np.linalg.norm(h.world(bpy.data.objects[n])-V,axis=1).max()) for n,V in toothWorld.items()}
  ob=bpy.data.objects[hairName];P=q.hair(ob).reshape(oldHair.shape);assert np.isfinite(P).all();radius=q.arr(ob.data.attributes['radius'].data,'value',24800*17);assert np.array_equal(radius,oldRadius)
  headEvidence=None
  if tag=='b':
   line=np.load(E/'b-native-head-lineage.npz');head=bpy.data.objects[ref['headObject']];V,T=evaluated(head);bodyV,bodyT=evaluated(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);assert np.isfinite(V).all() and np.array_equal(T,line['headTriangles'])
   readback=float(np.linalg.norm(P-line['hairNewWorld'],axis=2).max());assert readback<6e-6
   vi=np.column_stack([q.arr(ob.data.attributes['AFN97_ScalpVertex'+str(j)].data,'value',24800,dtype='i4') for j in range(3)]);w=q.arr(ob.data.attributes['AFN97_RootBarycentric'].data,'vector',24800,3).astype('f8');assert np.array_equal(vi,line['hairRootHeadVertices']) and np.all(w>=0) and np.max(abs(w.sum(1)-1))<2e-7
   tri=V[vi];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None];A=np.array(ob.matrix_world);rootR=q.arr(ob.data.attributes['AFN97_RootRadiusNative'].data,'value',24800);expected=np.sum(tri*w[:,:,None],axis=1)+normal*rootR[:,None]*np.linalg.norm(A[:3,0]);rootError=float(np.linalg.norm(P[:,0]-expected,axis=1).max());assert rootError<6e-6
   infos=[node.inputs['Object'].default_value for md in ob.modifiers if md.type=='NODES' for node in md.node_group.nodes if node.bl_idname=='GeometryNodeObjectInfo'];assert head in infos and bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'] not in infos
   neckError=float(np.linalg.norm(V[line['neckHeadVertexIDs']]-bodyV[line['neckBodyVertexIDs']],axis=1).max())
   headEvidence={'vertices':len(V),'triangles':len(T),'finite':True,'savedHairMaximumWorldErrorM':readback,'all24800RootsNumericalMaximumWorldErrorM':rootError,'actualEvaluatedBoundaryMaximumWorldErrorM':neckError,'hairFreeControlsMaximumWorldChangeFromR97M':float(np.linalg.norm(P[:,1:]-oldHair[:,1:],axis=2).max()),'actualRootGeometryNodeTargetsNewHead':True,'scope':'Numerical attachment on actual new head only. Coincident selected boundary vertices do not establish a welded manifold, nonoverlapping collar, smooth continuity or absence of visible holes. Original old-body head is a control cage, not the rendered new head contact surface.'}
  textures=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file:
    p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.is_file();textures.append({'relative':im.filepath,'sha256':sha(p)})
  assert len(textures)==15 and not bpy.data.libraries
  result[tag]={'source':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'independentlyReopened':True,'status':'MINIMUM_SAVED_DATA_ONLY_STRUCTURAL_APPEARANCE_REJECTED','originalOcularShellIrisRig52MaterialTreesAndLightsPreserved':True,'originalBodyNativeSignatureUnchanged':unchangedBody,'rigidTeethDataExact':tag=='b','actualRawToothWorldMaximumChangesM':toothD,'all24800SourceChildrenAndSourceRadiiCloseTipPreserved':True,'newHead':headEvidence,'externalTextures':textures,'appearanceCompleteOperationContactsNaturalDynamicsRuntimeAccepted':False};save('minimum-saved-readback.json',result);print('R98_MINIMUM_SAVED',tag,headEvidence,toothD,flush=True)
 save('verification-scope.json',{'seconds':time.time()-tick,'sourcesIndependentlyReopened':2,'broadAnimationAndContactAuditNotExpandedAfterVisibleStructuralFailure':True,'changedMotionDelivered':False,'reason':'A face/tooth deformation and B eyelid/neck construction rejected in the first actual complete previews. No qualified changed-motion claim; existing r97 rigid scalp-follow film does not apply to the new head.','actualRenderedFiniteRootBodySelfAndContinuousContacts':'UNACCEPTED_NOT_CERTIFIED','globalSignedMinimumM':None})
 print('R98_MINIMUM_REOPEN_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
