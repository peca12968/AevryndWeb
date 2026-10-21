"""Minimum independent coupled-source/blink recovery and capped neutral contact; no global claim."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,ast,time,os
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0120-ocular-socket-construction';S=R/'engine/assets/characters/female-next/source';OUT=S/'r0120-source/aevrynd-female-next-r0120-a-coupled-ocular-skin.blend'
sp=importlib.util.spec_from_file_location('r120readback',Path(__file__).with_name('build-female-next-r0120-ocular-skin-unit.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q
def main():
 tick=time.time();digest=a.a.a.sha(OUT);bpy.ops.wm.open_mainfile(filepath=str(OUT));skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];line=np.load(E/'ocular-skin-authoring-lineage.npz');changed=line['changedVertexIDs'];build=json.loads((E/'a-build-summary.json').read_text('utf-8'));A=np.array(skin.matrix_world);states=[];rest=None
 for name,value in [('neutral',0.),('half',.5),('closed',1.),('restored',0.)]:
  b.deliver(value);d,V,T=b.u.b.geom(skin);V=V.copy();T=T.copy();assert np.isfinite(V).all();expected=line['Basis_newLocal']+value*((line['AFN113_CLOSED_L_newLocal']-line['Basis_newLocal'])+(line['AFN113_CLOSED_R_newLocal']-line['Basis_newLocal']));expected=expected@A[:3,:3].T+A[:3,3];error=float(np.linalg.norm(V[changed]-expected,axis=1).max());assert error<2e-6
  if rest is None:rest=V.copy()
  lashes=q.hair(bpy.data.objects['AFN57_NATIVE_LASHES']);assert np.isfinite(lashes).all();states.append({'state':name,'assignedBlink':value,'actualChangedSkinAgainstAuthoredKeysMaxM':error,'actualSkinMaximumMoveM':float(np.linalg.norm(V-rest,axis=1).max()),'actualLashesFinite':True})
 assert states[-1]['actualSkinMaximumMoveM']==0;b.deliver(0);d,V,T=b.u.b.geom(skin);V=V.copy();T=T.copy();tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True,epsilon=0.);parsed=ast.parse(Path(__file__).with_name('verify-female-next-r0037-eye-margin.py').read_text('utf-8'));ns={'np':np};exec(compile(ast.Module(body=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ['inside','intersections']],type_ignores=[]),'same-r37-intersections','exec'),ns);contacts=[];eyeRows=[]
 z=np.load(E.parent/'r0119-anatomical-eye-rebuild/b-anatomical-eye-assembly-lineage.npz')
 for ob in bpy.data.objects:
  if not (ob.name.startswith('AFN119_') and ob.type=='MESH'):continue
  od,P,OT=b.u.b.geom(ob);P=P.copy();OT=OT.copy();error=float(np.linalg.norm(P-z[ob.name+'_world'],axis=1).max());assert error<2e-6;eyeRows.append({'name':ob.name,'actualAgainstFixedR119BMaxM':error});other=BVHTree.FromPolygons(P.tolist(),OT.tolist(),all_triangles=True,epsilon=0.);pairs=tree.overlap(other);hits=[];tested=0
  for i,j in pairs:
   pts=ns['intersections'](V[T[i]],P[OT[j]]);tested+=1
   if pts:hits.append({'skinTriangle':int(i),'eyeTriangle':int(j),'worldIntersectionOrTouchPointsM':[p.tolist() for p in pts[:4]]})
   if len(hits)>=8:break
  contacts.append({'pair':'actual complete skin vs '+ob.name,'state':'neutral','BVHCandidatePairs':len(pairs),'candidatePairsTestedUntilCap':tested,'storedIntersectionOrTouchWitnesses':len(hits),'cap':8,'witnesses':hits,'noRegionExcluded':True,'notGlobalSignedMinimumFiniteContainmentSelfOrContinuousProof':True})
 edge=np.sort(np.r_[T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]],axis=1);_,inc=np.unique(edge,axis=0,return_counts=True);textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath and im.users>0:
   p=Path(bpy.path.abspath(im.filepath));assert p.is_file(),str(p);textures.append({'name':im.name,'relative':im.filepath,'absolute':str(p),'sha256':a.a.a.sha(p),'bytes':p.stat().st_size})
 physical=Path('C:/Users/USER/AevryndCharacterSources/r0120')/OUT.name;archive=R/'sites-engine-journey/assets-source/aevrynd-character/female-next/r0120-source'/OUT.name;assert os.path.samefile(OUT,physical) and os.path.samefile(OUT,archive);assert a.a.a.sha(OUT)==digest
 a.save('minimum-saved-ocular-unit-readback.json',{'candidate':{'source':str(OUT),'sha256':digest,'bytes':OUT.stat().st_size,'physicalSource':str(physical),'archivePath':str(archive)},'status':'INDEPENDENT_REOPEN_AUTHORED_SKIN_KEYS_AND_FINITE_LASH_SAMPLES_RECOVERED_ONLY','actualPoseStates':states,'fixedR119EyeGeometry':eyeRows,'allSkinEdgesTwoIncident':bool(np.all(inc==2)),'closedEdgesNotSelfOrLayerThicknessProof':True,'allReferencedExternalTextures':textures,'contact':{'status':'UNACCEPTED_NEUTRAL_CAPPED_SURFACE_QUERY_ONLY','actualSurfaceWitnesses':contacts,'globalSignedMinimumM':None,'actualFiniteLashSkinSelfContainmentClosedPoseContinuousContactNotProved':True},'rawCoarseBodyIsReferenceOnlyHighResolutionSkinIsCurrentEditableSource':True,'sourceUnchangedDuringReadback':True,'completeOperationOrNaturalMotionRuntimeAccepted':False,'seconds':time.time()-tick});print('R120_COUPLED_SOURCE_INDEPENDENTLY_RECOVERED',[(x['pair'],x['storedIntersectionOrTouchWitnesses']) for x in contacts],time.time()-tick,flush=True)
if __name__=='__main__':main()
