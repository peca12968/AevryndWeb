from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0183-upper-anterior-root-bands'
sp=importlib.util.spec_from_file_location('r179',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
b=json.loads((E/'a-build-summary.json').read_text());t=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=t['source']);bpy.context.scene.frame_set(1);bpy.data.objects[a.FIXED[1]].material_slots[0].link='DATA';bpy.context.view_layer.update();raw={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert raw=={n:a.rawsig(bpy.data.objects[n]) for n in raw};skin=bpy.data.objects[b['actualSkin']];lash=bpy.data.objects[b['actualHair']];rig=bpy.data.objects[b['actualRig']];P,offset=m.curveworld(lash);initial=P.copy();birth=h.arr(lash.data.attributes['AFN183_FOLLICLE_ID'].data,'value',len(offset),dtype='i4');assert np.array_equal(birth,np.arange(436));line=np.load(E/'upper-anterior-band-lineage.npz');rT=line['rootTriangles'];bc=line['rootBC'];W,T=a.geometry(skin);eyeW,eyeT=a.geometry(bpy.data.objects[a.MOVING[0]]);record=[];witness=[];normError=[]
for frame in range(1,50):
 s.frame_set(frame);bpy.context.view_layer.update();pos,off=m.curveworld(lash);assert np.array_equal(off,offset)
 dg=bpy.context.evaluated_depsgraph_get();ev=skin.evaluated_get(dg);V=h.arr(ev.data.vertices,'co',len(ev.data.vertices),3);V=V@np.array(skin.matrix_world)[:3,:3].T+np.array(skin.matrix_world.translation);B=V[rT];root=(B*bc[:,:,None]).sum(1);no=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);no/=np.linalg.norm(no,axis=1,keepdims=True);expected=root+no*.000032;error=float(np.linalg.norm(pos[offset]-expected,axis=1).max());normError.append(error);record.append({'frame':frame,'actualEyeEulerDegrees':a.angles(rig),'maximumDisplayedLashMovementM':float(np.linalg.norm(pos-initial,axis=1).max()),'all436PrescribedRadiusRootMaximumErrorM':error})
 if frame in [1,13,37]:
  mask=(V[T].mean(1)[:,2]>1.435)&(V[T].mean(1)[:,2]<1.50)&(np.abs(V[T].mean(1)[:,0])<.065);faces=np.flatnonzero(mask);tree=BVHTree.FromPolygons(V.tolist(),T[faces].tolist(),all_triangles=True);points=pos.reshape(436,17,3);count=0;rows=[]
  for cid,path in enumerate(points):
   for j in range(16):
    d=path[j+1]-path[j];length=float(np.linalg.norm(d))
    if length<1e-10:continue
    q,n,fi,dist=tree.ray_cast(Vector(path[j]),Vector(d/length),length)
    if q is not None and 1e-7<float(dist)<length-1e-7:
     count+=1
     if len(rows)<10:rows.append({'curveID':cid,'controlChord':j,'actualSkinTriangle':int(faces[fi]),'point':list(q),'distanceAlongChordM':float(dist),'chordLengthM':length})
  ocular=[]
  for eyeName in a.MOVING:
   eW,eT=a.geometry(bpy.data.objects[eyeName]);eTree=BVHTree.FromPolygons(eW.tolist(),eT.tolist(),all_triangles=True);eCount=0;eRows=[]
   for cid,path in enumerate(points):
    for j in range(16):
     d=path[j+1]-path[j];length=float(np.linalg.norm(d))
     if length<1e-10:continue
     hit,no,fi,along=eTree.ray_cast(Vector(path[j]),Vector(d/length),length)
     if hit is not None and 1e-7<float(along)<length-1e-7:
      eCount+=1
      if len(eRows)<5:eRows.append({'curveID':cid,'controlChord':j,'eyeTriangle':int(fi),'point':list(hit)})
   ocular.append({'actualEyeObject':eyeName,'controlChordIntersections':eCount,'firstFive':eRows})
  fullTree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);radius=h.arr(lash.data.attributes['radius'].data,'value',len(pos));gaps=np.array([fullTree.find_nearest(Vector(p))[3] for p in pos])-radius;bad=np.flatnonzero(gaps < -1e-6);finite={'actualFullSkinTriangles':len(T),'allControlPointsIncludingRoots':len(pos),'sampledUnsignedSurfaceMinusRadiusQuantilesM':np.quantile(gaps,[0,.5,.99,1]).tolist(),'pointsBelowMinus1um':len(bad),'firstTenPointIDs':bad[:10].tolist(),'notInsideProofOrExactRenderedFiniteSplineCertificate':True};witness.append({'fullSkinPointRadiusProxy':finite,'ocularMeshChordLocators':ocular,'frame':frame,'actualRegionalSkinTriangles':len(faces),'all436CurveControlChordsTested':True,'strongControlChordIntersections':count,'firstTenLocations':rows,'notExactRenderedFiniteSplineOrSelfContinuousTest':True})
s.frame_set(1);bpy.context.view_layer.update();rest,_=m.curveworld(lash);actionRestore=float(np.linalg.norm(rest-initial,axis=1).max());assert actionRestore<3e-6 and max(normError)<3e-6
point=16;p=lash.data.position_data[point].vector.copy();lash.data.position_data[point].vector.x+=.001;lash.data.update_tag();lash.update_tag();bpy.context.view_layer.update();move,_=m.curveworld(lash);pointMove=float(np.linalg.norm(move-initial,axis=1).max());lash.data.position_data[point].vector=p;lash.data.update_tag();lash.update_tag();bpy.context.view_layer.update();rest,_=m.curveworld(lash);pointRestore=float(np.linalg.norm(rest-initial,axis=1).max());assert pointMove>1e-6 and pointRestore<3e-6
material=lash.data.materials[0];node=next(n for n in material.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfHairPrincipled');deps=[{'path':bpy.path.abspath(x.filepath),'exists':Path(bpy.path.abspath(x.filepath)).exists()} for x in bpy.data.libraries];assert all(x['exists'] for x in deps)
rootDistances=np.linalg.norm(initial[offset][:,None]-initial[offset][None],axis=2);np.fill_diagonal(rootDistances,np.inf);duplicates=np.argwhere(np.triu(rootDistances<1e-7,1));coincident=[{'a':int(i),'b':int(j),'distanceM':float(rootDistances[i,j])} for i,j in duplicates]
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':b['output'],'sourceSHA256':a.a.sha(Path(b['output'])),'originalSevenMeshUVSignaturesEqual':True,'actualDisplayedLashCurves':436,'actualDisplayedPoints':len(initial),'persistentComponentIDsExact':True,'actualOriginalGazeFrames1Through49Completed':record,'all436RadiusRootConstraintMaximumErrorM':max(normError),'actualActionNeutralRestoreMaximumM':actionRestore,'nativeTip1mmEditMovementM':pointMove,'nativeTipEditRestoreMaximumM':pointRestore,'regionalSkinControlChordWitnesses':witness,'completeVisualGazeFiniteContactNaturalDynamicsRuntimeUnaccepted':True,'globalSignedMinimumM':None,'coincidentEvaluatedRootCentrePairs':coincident,'minimumDistinctRootCentreDistanceM':float(rootDistances.min()),'duplicateRootConstructionNotExactRenderedSelfContactCount':True,'actualCurveAttributeSchema':[{'name':x.name,'domain':x.domain,'dataType':x.data_type} for x in lash.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.attributes],'actualFixedMaterialReadback':{'actualMaterial':material.name,'actualParametrization':node.parametrization,'actualMelanin':node.inputs['Melanin'].default_value,'actualMelaninRedness':node.inputs['Melanin Redness'].default_value,'actualRoughness':node.inputs['Roughness'].default_value,'actualRadialRoughness':node.inputs['Radial Roughness'].default_value,'notAnOpticsVariant':True},'actualCloseupCaptureControls':{'baseline':str(E.parent/'r0182-anterior-surface-root-band/corrected-anterior-band-eye-capture-controls.json'),'candidate':str(E/'upper-band-eye-capture-controls.json'),'baselineControls':json.loads((E.parent/'r0182-anterior-surface-root-band/corrected-anterior-band-eye-capture-controls.json').read_text()),'candidateControls':json.loads((E/'upper-band-eye-capture-controls.json').read_text()),'prior179ImagesAndDefectiveMetadataUntouched':True},'dependencies':deps,'fileUnmodifiedByVerification':a.a.sha(Path(b['output']))==b['sha256']}
(E/'independent-upper-band-readback.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R183_INDEPENDENT_UPPER_BANDS_49_GAZE_EDIT_RESTORE_DONE',flush=True)
