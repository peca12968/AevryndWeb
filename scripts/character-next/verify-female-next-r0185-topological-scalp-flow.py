"""Minimum independent reopen/edit/restore and cheap failure locators only."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0185-topological-scalp-flow'
sp=importlib.util.spec_from_file_location('r169',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
b=json.loads((E/'a-build-summary.json').read_text());t=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=t['source']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};hair=bpy.data.objects[b['actualHair']];skin=bpy.data.objects[b['actualSkin']];data=hair.data;P,off=m.curveworld(hair);birth=h.arr(data.attributes['AFN185_FOLLICLE_ID'].data,'value',len(off),dtype='i4');assert len(off)==64000 and len(P)==2112000 and np.array_equal(birth,np.arange(64000));assert np.isfinite(P).all();native=h.arr(data.position_data,'vector',len(P),3);assert np.array_equal(native,P);assert not hair.modifiers
line=np.load(E/'topological-scalp-flow-lineage.npz');W,T=a.geometry(skin);tri=line['rootTriangles'];bc=line['rootBC'];vn=np.zeros_like(W);sf=line['scalpFaces'];cr=np.cross(W[T[sf,1]]-W[T[sf,0]],W[T[sf,2]]-W[T[sf,0]])
for j in range(3):np.add.at(vn,T[sf,j],cr)
vn/=np.maximum(np.linalg.norm(vn,axis=1,keepdims=True),1e-15);normal=(vn[tri]*bc[:,:,None]).sum(1);normal/=np.linalg.norm(normal,axis=1,keepdims=True);root=(W[tri]*bc[:,:,None]).sum(1);expected=root+normal*.000035;rootError=float(np.linalg.norm(P[off]-expected,axis=1).max());assert rootError<3e-6
point=32;old=data.position_data[point].vector.copy();data.position_data[point].vector.x+=.001;data.update_tag();hair.update_tag();bpy.context.view_layer.update();moved,off2=m.curveworld(hair);assert np.array_equal(off,off2);movement=float(np.linalg.norm(moved-P,axis=1).max());data.position_data[point].vector=old;data.update_tag();hair.update_tag();bpy.context.view_layer.update();rest,off3=m.curveworld(hair);restore=float(np.linalg.norm(rest-P,axis=1).max());assert movement>.0009 and restore==0 and np.array_equal(off,off3);assert np.array_equal(birth,h.arr(data.attributes['AFN185_FOLLICLE_ID'].data,'value',64000,dtype='i4'))
tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True);tested=np.linspace(0,63999,256,dtype=int);locations=[];chords=0;pointGaps=[];radius=h.arr(data.attributes['radius'].data,'value',len(P));Q=P.reshape(64000,33,3)
for cid in tested:
 for j,p in enumerate(Q[cid]):pointGaps.append(float(tree.find_nearest(Vector(p))[3])-float(radius[cid*33+j]))
 for j in range(32):
  dd=Q[cid,j+1]-Q[cid,j];length=float(np.linalg.norm(dd))
  if length<1e-9:continue
  hit,no,fi,along=tree.ray_cast(Vector(Q[cid,j]),Vector(dd/length),length)
  if hit is not None and 1e-7<float(along)<length-1e-7:
   chords+=1
   if len(locations)<12:locations.append({'curveID':int(cid),'controlChord':j,'actualSkinTriangle':int(fi),'point':list(hit),'distanceAlongM':float(along)})
deps=[{'path':bpy.path.abspath(x.filepath),'exists':Path(bpy.path.abspath(x.filepath)).exists()} for x in bpy.data.libraries];assert all(x['exists'] for x in deps)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':b['output'],'sourceSHA256':a.a.sha(Path(b['output'])),'originalSevenRawMeshUVSignaturesEqual':True,'nativeCurveCount':64000,'actualDisplayedPoints':len(P),'actualNativeAndEvaluatedAllPositionsExactlyEqual':True,'noGeometryModifiers':True,'persistentAll64000CurveIDsAndOffsetsExact':True,'all64000ActualScalpRootCentreMaximumErrorM':rootError,'nativeTip1mmActualMovementM':movement,'nativeTipEditRestoreMaximumM':restore,'originalLashesVisible':not bpy.data.objects[a.FIXED[2]].hide_render,'unaccepted184LashesHidden':bpy.data.objects['AFN184_ACTUAL_NATIVE_DEFORMED_LASHES'].hide_render,'originalHairHiddenRollback':bpy.data.objects[a.FIXED[1]].hide_render,'actualNewHairVisible':not hair.hide_render,'sampledRestSkinControlChordFailureLocators':{'sampledWholeFibres':len(tested),'all33PointsIncludingRootsEach':True,'controlChordIntersections':chords,'first12':locations,'pointUnsignedDistanceMinusRadiusMinimumM':min(pointGaps),'pointsBelowMinus1um':sum(x < -1e-6 for x in pointGaps),'notExactRenderedFiniteSplineSelfContinuousOrGlobalSignedProof':True},'headFollowNaturalDynamicsRuntimeNotClaimed':True,'globalSignedMinimumM':None,'dependencies':deps,'fileUnmodified':a.a.sha(Path(b['output']))==b['sha256'],'minimumOnlyAfterVisibleFailure':True}
(E/'independent-topological-rest-readback.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R185_MINIMUM_INDEPENDENT_REOPEN_EDIT_RESTORE_FAILURE_LOCATORS_DONE',flush=True)
