from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0177-anatomical-guide-paths'
sp=importlib.util.spec_from_file_location('r177',C/'scripts/character-next/build-female-next-r0177-anatomical-guide-paths.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
b=json.loads((E/'a-build-summary.json').read_text());timing=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=timing['source']);bpy.context.scene.frame_set(1);bpy.data.objects[a.FIXED[1]].material_slots[0].link='DATA';bpy.context.view_layer.update();baseline={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
bpy.ops.wm.open_mainfile(filepath=b['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects[b['actualHair']];go=bpy.data.objects[b['actualGuides']];skin=bpy.data.objects[b['actualSkin']];assert baseline=={n:a.rawsig(bpy.data.objects[n]) for n in baseline};P,offset=m.m.curveworld(hair);initial=P.copy();birth=h.arr(hair.data.attributes['AFN177_BIRTH_ID'].data,'value',len(offset),dtype='i4');assert np.array_equal(birth,np.arange(10191));idsHash=a.a.hasharray(birth)
def evalhair():bpy.context.view_layer.update();return m.m.curveworld(hair)[0]
point=16;original=go.data.position_data[point].vector.copy();go.data.position_data[point].vector.x+=.001;go.data.update_tag();go.update_tag();moved=evalhair();movement=float(np.linalg.norm(moved-initial,axis=1).max());assert movement>1e-6;go.data.position_data[point].vector=original;go.data.update_tag();go.update_tag();restore=float(np.linalg.norm(evalhair()-initial,axis=1).max());assert restore<3e-6
line=np.load(E/'anatomical-guide-path-lineage.npz');W,T=a.geometry(skin);rT=line['rootTriangles'];rBC=line['rootBC'];B=W[rT];normal=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);normal/=np.linalg.norm(normal,axis=1,keepdims=True);root=(B*rBC[:,:,None]).sum(1);expected=root+normal*.000035;rootError=float(np.linalg.norm(initial[offset]-expected,axis=1).max());assert rootError<3e-6
# One bounded locator on known ear/head sample curves; control chords only.
tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True);witness=[]
for cid in [80,240,320,int(np.argmin(np.linalg.norm(root-line['guideWorld'][61,0],axis=1)))]:
 path=initial[offset[cid]:offset[cid]+33]
 for j in range(32):
  d=path[j+1]-path[j];length=float(np.linalg.norm(d))
  if length<1e-10:continue
  loc,no,fi,dist=tree.ray_cast(Vector(path[j]),Vector(d/length),length)
  if loc is not None and 1e-6<float(dist)<length-1e-6:witness.append({'curveID':cid,'controlChord':j,'bodyTriangle':int(fi),'point':list(loc),'chordLengthM':length,'distanceAlongChordM':float(dist)})
deps=[]
for lib in bpy.data.libraries:
 p=Path(bpy.path.abspath(lib.filepath));deps.append({'path':str(p),'exists':p.exists()})
assert all(x['exists'] for x in deps)
record={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':b['output'],'sourceSHA256':a.a.sha(Path(b['output'])),'originalSevenMeshUVSignaturesEqual':True,'actualHair':hair.name,'actualGuides':go.name,'actualDisplayedCurves':len(offset),'actualDisplayedPoints':len(initial),'persistentBirthIDHash':idsHash,'persistentBirthIDs0To10190Exact':True,'nativeGuide0Point16Edit1mmDisplayMaximumMovementM':movement,'nativeGuideEditRestoreMaximumM':restore,'allRootCentrePrescribedRadiusErrorMaximumM':rootError,'guideEditingOnlyNotCompleteNaturalHairOperation':True,'originalWomanAndGazeDataPreservedNoNew49PoseTestClaim':True,'sampledCurveControlChordBodyWitnesses':witness,'notExactRenderedSplineFiniteThicknessSelfOrContinuousContactTest':True,'fullFiniteSelfContinuousNaturalMotionRuntimeUnaccepted':True,'dependencies':deps,'fileUnmodifiedByVerification':a.a.sha(Path(b['output']))==b['sha256']}
(E/'independent-anatomical-guide-readback.json').write_text(json.dumps(record,indent=2)+'\n','utf-8');print('R177_INDEPENDENT_COMPLETE_SOURCE_GUIDE_EDIT_RESTORE_DONE',flush=True)
