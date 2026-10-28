"""Individually authored complete current-space Bezier trajectories.
Only current-Skin birth/ID/generator construction is inherited; no old free path.
Bezier controls are build-time construction. Actual editable controls are the
252 native raw guides, independently verified against displayed10191 children.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,time,importlib.util,shutil
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
access=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(access['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0203-current-space-bezier-groom';F=Path('F:/AevryndEvidence/r0203-current-space-bezier-groom');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,d):(E/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);sp=importlib.util.spec_from_file_location('r203base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];hair=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];births=bpy.data.objects['AFN198_ACTUAL_EDITABLE_SURFACE_BIRTHS'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};before=h.arr(hair.data.position_data,'vector',4032,3).reshape(252,16,3);roots=before[:,0].copy()
# Explicit independent artistic spatial paths, in metres on the actual woman.
# Each row is one full3D path with three cubic Bezier segments,10 controls.
paths=[
('L_forehead',[-.008,-.097,1.554,-.025,-.111,1.580,-.058,-.135,1.553,-.078,-.128,1.520,-.10,-.128,1.490,-.138,-.112,1.510,-.132,-.094,1.470,-.120,-.084,1.430,-.084,-.086,1.400,-.105,-.058,1.360]),
('L_frontal_crown',[-.011,-.065,1.570,-.040,-.066,1.605,-.089,-.104,1.585,-.097,-.110,1.541,-.101,-.119,1.496,-.145,-.085,1.497,-.132,-.070,1.455,-.112,-.060,1.412,-.119,-.046,1.366,-.091,-.032,1.345]),
('L_temporal_top',[-.055,-.071,1.544,-.076,-.077,1.568,-.112,-.089,1.551,-.117,-.081,1.509,-.12,-.071,1.464,-.140,-.044,1.449,-.126,-.037,1.417,-.112,-.030,1.384,-.097,-.045,1.354,-.092,-.022,1.335]),
('L_temple',[-.066,-.087,1.513,-.081,-.090,1.539,-.110,-.101,1.523,-.113,-.094,1.488,-.117,-.086,1.455,-.137,-.060,1.449,-.125,-.047,1.420,-.111,-.030,1.391,-.121,-.032,1.363,-.099,-.018,1.343]),
('L_lateral_crown',[-.038,-.016,1.558,-.064,-.011,1.590,-.110,-.014,1.559,-.119,-.008,1.517,-.13,-.001,1.474,-.137,.016,1.466,-.132,.020,1.429,-.123,.019,1.393,-.106,.004,1.367,-.110,.028,1.342]),
('L_lateral_ear',[-.073,-.018,1.490,-.086,-.014,1.521,-.119,-.012,1.504,-.122,-.004,1.476,-.128,.006,1.449,-.143,.023,1.436,-.128,.027,1.407,-.112,.031,1.379,-.105,.019,1.355,-.096,.036,1.335]),
('L_rear_crown',[-.024,.025,1.559,-.044,.051,1.580,-.076,.079,1.553,-.077,.085,1.509,-.079,.095,1.465,-.112,.094,1.452,-.103,.086,1.415,-.096,.078,1.379,-.075,.063,1.345,-.067,.079,1.330]),
('L_rear_upper',[-.052,.031,1.532,-.071,.054,1.552,-.099,.076,1.523,-.100,.085,1.487,-.105,.094,1.451,-.120,.089,1.443,-.110,.079,1.409,-.098,.070,1.376,-.086,.072,1.354,-.078,.055,1.332]),
('L_behind_ear',[-.071,.026,1.473,-.088,.044,1.493,-.107,.071,1.473,-.112,.074,1.446,-.119,.079,1.418,-.110,.091,1.403,-.100,.081,1.381,-.091,.073,1.358,-.069,.068,1.350,-.065,.077,1.334]),
('L_nape',[-.039,.033,1.425,-.055,.049,1.433,-.069,.070,1.418,-.067,.075,1.391,-.065,.080,1.371,-.055,.085,1.352,-.046,.076,1.344,-.037,.067,1.334,-.034,.057,1.328,-.025,.066,1.319]),
('L_centre_back',[-.006,.049,1.521,-.009,.074,1.535,-.017,.094,1.510,-.022,.100,1.475,-.027,.109,1.440,-.043,.099,1.425,-.038,.091,1.395,-.029,.083,1.363,-.022,.079,1.343,-.017,.066,1.326]),
('R_forehead',[.009,-.095,1.555,.028,-.112,1.579,.061,-.127,1.561,.076,-.123,1.525,.091,-.119,1.489,.128,-.108,1.489,.131,-.085,1.461,.135,-.061,1.431,.103,-.055,1.410,.113,-.038,1.381]),
('R_frontal_crown',[.012,-.061,1.570,.044,-.061,1.602,.090,-.090,1.584,.103,-.101,1.543,.119,-.109,1.502,.139,-.076,1.488,.128,-.060,1.456,.117,-.043,1.422,.131,-.034,1.384,.108,-.017,1.359]),
('R_temporal_top',[.052,-.071,1.546,.076,-.073,1.572,.110,-.082,1.547,.121,-.071,1.513,.13,-.061,1.477,.136,-.036,1.453,.124,-.028,1.422,.112,-.018,1.389,.109,-.035,1.366,.095,-.015,1.345]),
('R_temple',[.065,-.084,1.513,.080,-.089,1.536,.112,-.091,1.516,.116,-.081,1.484,.123,-.071,1.452,.134,-.048,1.434,.122,-.034,1.408,.111,-.019,1.382,.114,-.007,1.364,.097,.001,1.347]),
('R_lateral_crown',[.035,-.014,1.560,.065,-.005,1.590,.110,.000,1.563,.119,.006,1.522,.128,.011,1.479,.137,.033,1.458,.123,.034,1.426,.108,.037,1.392,.106,.020,1.365,.100,.044,1.341]),
('R_lateral_ear',[.073,-.016,1.491,.086,-.005,1.516,.116,.009,1.498,.123,.017,1.470,.131,.026,1.439,.139,.041,1.427,.126,.047,1.402,.112,.053,1.375,.098,.039,1.353,.090,.051,1.338]),
('R_rear_crown',[.021,.026,1.559,.042,.054,1.584,.070,.079,1.549,.076,.087,1.513,.083,.095,1.474,.112,.095,1.450,.100,.084,1.416,.088,.075,1.381,.072,.084,1.350,.066,.063,1.332]),
('R_rear_upper',[.050,.035,1.531,.069,.056,1.550,.095,.079,1.524,.098,.087,1.485,.102,.094,1.446,.116,.092,1.430,.104,.083,1.402,.092,.072,1.373,.077,.077,1.355,.071,.062,1.337]),
('R_behind_ear',[.070,.027,1.474,.084,.047,1.490,.103,.072,1.470,.107,.078,1.440,.112,.083,1.411,.107,.094,1.395,.094,.085,1.376,.081,.076,1.355,.064,.071,1.347,.058,.082,1.331]),
('R_nape',[.036,.034,1.424,.048,.052,1.433,.065,.073,1.414,.065,.078,1.389,.065,.083,1.367,.052,.090,1.354,.043,.080,1.342,.035,.072,1.331,.028,.057,1.330,.020,.063,1.320]),
('R_centre_back',[.006,.049,1.521,.012,.072,1.540,.021,.096,1.509,.024,.103,1.474,.027,.111,1.438,.041,.103,1.419,.035,.095,1.391,.029,.086,1.362,.021,.077,1.343,.014,.067,1.328])]
control=np.array([p for _,p in paths],dtype='f8').reshape(-1,10,3);names=[n for n,_ in paths];K=len(control)
def evaluate(C,ts):
 out=[]
 for u in ts:
  segment=min(int(u*3),2);v=u*3-segment;P=C[segment*3:segment*3+4];out.append((1-v)**3*P[0]+3*(1-v)**2*v*P[1]+3*(1-v)*v*v*P[2]+v**3*P[3])
 return np.array(out)
def path_sample(C):
 dense=evaluate(C,np.linspace(0,1,385));arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))];u=np.linspace(0,arc[-1],16);return np.column_stack([np.interp(u,arc,dense[:,k]) for k in range(3)])
B=np.array([path_sample(C) for C in control]);anchors=control[:,0];authored=[];mapids=[];mapweights=[];u=np.linspace(0,1,16)
for root in roots:
 candidates=np.flatnonzero(np.array([n.startswith('R_') for n in names])==(root[0]>=0));d=np.linalg.norm(anchors[candidates]-root,axis=1);ix=np.argsort(d)[:3];ids=candidates[ix];w=1/np.maximum(d[ix],.004)**3;w/=w.sum();P=np.einsum('n,nij->ij',w,B[ids]);anchor=w@anchors[ids];P+=(root-anchor)[None,:]*(1-u[:,None])**2;P[0]=root;authored.append(P);mapids.append(ids);mapweights.append(w)
P=np.array(authored,dtype='f4');assert np.isfinite(P).all() and np.max(np.linalg.norm(P[:,0]-roots,axis=1))==0;hair.data.position_data.foreach_set('vector',P.ravel());hair.data.update_tag();bpy.context.view_layer.update()
# Build-time Bezier controls retained with semantic names; not claimed as live
# modifiers. Native252 guide positions are the actual operative editor.
coll=bpy.data.collections.new('AFN203_BUILD_TIME_BEZIER_CONSTRUCTION');s.collection.children.link(coll)
for i,(name,C) in enumerate(zip(names,control)):
 cu=bpy.data.curves.new('AFN203_BEZIER_'+name,'CURVE');cu.dimensions='3D';sp=cu.splines.new('BEZIER');sp.bezier_points.add(3)
 for j,p in enumerate(sp.bezier_points):
  p.co=C[j*3];p.handle_left_type='FREE';p.handle_right_type='FREE';p.handle_left=C[j*3-1] if j else 2*C[0]-C[1];p.handle_right=C[j*3+1] if j<3 else 2*C[9]-C[8]
 ob=bpy.data.objects.new(cu.name,cu);coll.objects.link(ob);ob.hide_render=True;ob.hide_set(True);ob['scope']='Build-time authoring reference; rebuild script resamples into operative252 native raw guides.'
hair['AFN203_AUTHORING']='Complete22 individually defined native current-space Bezier path construction, barycentric currentSkin roots unchanged; raw252 guides actually drive displayed10191 curves.';hair['AFN203_BUILD_TIME_PATH_COUNT']=K
actual,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(off),2);lineage=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz');assert len(off)==10191 and np.array_equal(np.sort(ids),np.arange(10191));rootError=float(np.linalg.norm(actual[off]-lineage['shaftStartWorld'][ids],axis=1).max());assert rootError<3e-6;assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
V,T=a.geometry(old);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);referenceDistances=np.array([tree.find_nearest(Vector(q))[3] for curve in B for q in curve]);np.savez_compressed(E/'current-space-bezier-authored-lineage.npz',authorBezierControlWorld=control,authorPathSamples=B,authorPathNames=np.array(names),guideAuthorPathIDs=np.array(mapids),guideAuthorPathWeights=np.array(mapweights),actualGuideAuthoredPositions=P,originalGuideRoots=roots,oldFailedGuidePaths=before,displayBirthIDs=ids,displayBirthUV=uv,actualDisplayedPositions=actual,actualDisplayedOffsets=off,referenceSampleSurfaceDistancesM=referenceDistances)
save('complete-bezier-construction.json',{'UTC':stamp(),'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'buildTimeBezierPaths':K,'operativeNativeGuides':252,'actualDisplayedCurves':len(off),'actualDisplayedPoints':len(actual),'rootMaximumChangeM':0,'freePathMaximumChangeM':float(np.linalg.norm(P-before,axis=2).max()),'displayRootMaximumCorrespondenceErrorM':rootError,'all10191PersistentBirthIDsRetained':True,'allSevenRawMeshUVSignaturesUnchanged':protected,'currentGuideRootsAndActualBirthTrianglesUVNotMoved':True,'actualSameWomanOriginalHairSurfaceReferenceDistanceQuantilesM':np.quantile(referenceDistances,[0,.5,.9,1]).tolist(),'surfaceReferenceDistanceNotAppearanceOrContactProof':True,'completeNewOwnRestPathsNotForeignRootsOrUV':True,'noInheritedFailedFreePathRescue':True,'materialAndRadiiUnchanged':'AFN198_OWN_NATIVE_HAIR_FIXED_MELANIN, original fixed generator radii','actualEditableControl':'252 raw native guide positions; build-time22 Bezier paths resampled by rebuild script, not live linked handles.','constructionSecondsBeforePreview':time.time()-tick})
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(v) for v in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'exposure':scene.view_settings.exposure,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'cyclesSamples':scene.cycles.samples,'seed':scene.cycles.seed,'originalHairVisible':not old.hide_render,'nativeGroomVisible':not hair.hide_render,'captureStateNotRenderGeometryDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=F;hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
old.hide_render=True;hair.hide_render=False;hair.hide_set(False)
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('a-current-space-bezier-groom',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP'
for f in F.glob('matched-*.png'):shutil.copyfile(f,E/f.name)
output=F/'aevrynd-female-next-r0203-current-space-bezier-groom.blend';out=A/'assets-source/aevrynd-character/female-next/r0203-source'/output.name;out.parent.mkdir();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);shutil.copyfile(output,out);assert sha(out)==sha(output)
save('a-build-summary.json',{'UTC':stamp(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'oneCompleteCandidate':True,'actualCurves':len(off),'actualPoints':len(actual),'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'elapsedJobSeconds':time.time()-tick,'unaccepted':True});print('R203_COMPLETE_CURRENT_SPACE_BEZIER_CANDIDATE_SAVED',json.dumps({'source':str(output),'curves':len(off),'points':len(actual),'rawChangeM':float(np.linalg.norm(P-before,axis=2).max())}),flush=True)