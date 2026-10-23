from pathlib import Path
import bpy,numpy as np,importlib.util,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0177-anatomical-guide-paths'
sp=importlib.util.spec_from_file_location('base177',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a
b=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];W,T=a.geometry(skin)
x=np.load(E.parent/'r0169-native-carrier-groom/coherent-native-carrier-lineage.npz');y=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz');faces=y['actualScalpFaces'];cap=W[np.unique(T[faces])];SV=x['sourceCarrierWorld'];ST=x['sourceCarrierTriangles'];G=x['sourcePosedGuides'].reshape(252,16,3);SR=G[:,0]
# Anatomical registration seeds: measured head summit and full head lateral extent.
sourceHead=SV[SV[:,2]>1.53];targetHead=W[(W[:,2]>1.45)&(abs(W[:,0])<.15)]
sourceSummit=SV[np.argmax(SV[:,2])];targetSummit=targetHead[np.argmax(targetHead[:,2])];shift=targetSummit-sourceSummit
tree=BVHTree.FromPolygons(W.tolist(),T[faces].tolist(),all_triangles=True);root=[];tri=[];bc=[];norm=[];gaps=[]
for p in SR:
 q,n,fi,d=tree.find_nearest(Vector(p+shift));B=W[T[faces[fi]]];v=np.linalg.lstsq(np.column_stack((B[1]-B[0],B[2]-B[0])),np.array(q)-B[0],rcond=None)[0];root.append(q[:]);tri.append(T[faces[fi]]);bc.append([1-v.sum(),*v]);norm.append(n[:]);gaps.append(d)
np.savez_compressed(E/'anatomical-source-current-root-correspondence.npz',currentWorld=W,currentTriangles=T,scalpFaces=faces,guideTriangles=np.array(tri),guideBC=np.array(bc),guideRoot=np.array(root),guideNormal=np.array(norm),summitTranslation=shift)
record={'sourceSummit':sourceSummit.tolist(),'currentSummit':targetSummit.tolist(),'rootSearchSeedTranslationOnly':shift.tolist(),'rootToScalpSearchGapM':gaps,'root0and61':{'sourceRoots':SR[[0,61]].tolist(),'sourceTips':G[[0,61],-1].tolist(),'currentRoots':np.array(root)[[0,61]].tolist(),'currentNormals':np.array(norm)[[0,61]].tolist()},'seedNotWholeHairTransform':True,'proposedConstruction':'Independent true artist guide root-to-tip paths transported by each matched anatomical surface normal, with actual root triangle ownership. No UV derivative, carrier tangent or decorative hair inversion; inspect root landmarks before adoption.'}
(E/'anatomical-correspondence-inspection.json').write_text(json.dumps(record,indent=2)+'\n')
# Actual source and current anatomical scalp geometry, common metric coordinates.
for ob in s.objects:
 if ob.type not in ['CAMERA','LIGHT']:ob.hide_render=True
for i,(V,F) in enumerate([(SV,ST),(W,T)]):
 keep=np.all(V[F,2]>(1.48 if i==0 else 1.40),axis=1);v=V.copy();v[:,0]+=(i-.5)*.32;v[:,2]-=0 if i else -shift[2]
 mesh=bpy.data.meshes.new('AFN177_DIAGNOSTIC_ANATOMICAL_HEAD');mesh.from_pydata(v.tolist(),[],F[keep].tolist());ob=bpy.data.objects.new('AFN177_DIAGNOSTIC_HEAD_'+str(i),mesh);s.collection.objects.link(ob)
 mat=bpy.data.materials.new('AFN177_DIAGNOSTIC_MAT');mat.diffuse_color=(.18,.36,.48,1) if i==0 else (.48,.3,.17,1);ob.data.materials.append(mat)
 for j in [0,61]:
  p=(SR if i==0 else np.array(root))[j].copy();p[0]+=(i-.5)*.32;p[2]-=0 if i else -shift[2];bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.003,location=p);bpy.context.object.name=f'AFN177_DIAGNOSTIC_ROOT_{i}_{j}';bpy.context.object.data.materials.append(mat)
cam=s.camera;cam.location=(.28,-1.1,1.62);target=Vector((0,0,1.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.68;s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.cycles.samples=12;s.render.filepath=str(E/'actual-source-current-anatomical-head-root-landmarks.png');bpy.ops.render.render(write_still=True)
print('R177_ACTUAL_ANATOMICAL_ROOT_INSPECTION_DONE',flush=True)
