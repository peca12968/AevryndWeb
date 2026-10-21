"""Locate retained capped witnesses in actual native skin topology before authoring."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0120-ocular-socket-construction';PRE=E.parent/'r0119-anatomical-eye-rebuild';SRC=R/'engine/assets/characters/female-next/source/r0119-source/aevrynd-female-next-r0119-b-native-iris-landmark-eyes.blend'
sp=importlib.util.spec_from_file_location('r120inspect',Path(__file__).with_name('build-female-next-r0119-anatomical-eyes.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];raw=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];d,W,T=b.u.b.geom(skin);P=q.arr(d.loop_triangles,'polygon_index',len(T),dtype='i4');parents=q.arr(d.attributes['AFN117_NATIVE_PARENT_FACE'].data,'value',len(d.polygons),dtype='i4');A=np.array(raw.matrix_world);V=q.arr(raw.data.vertices,'co',len(raw.data.vertices),3)@A[:3,:3].T+A[:3,3];rows=[]
 for pair in json.loads((PRE/'minimum-saved-eye-assembly-readback.json').read_text('utf-8'))['sources']['b']['contact']['actualSurfaceWitnesses']:
  for hit in pair['witnesses']:
   ti=hit['skinTriangle'];tr=T[ti];n=np.cross(W[tr[1]]-W[tr[0]],W[tr[2]]-W[tr[0]]);n/=np.linalg.norm(n);parent=int(parents[P[ti]]);f=list(raw.data.polygons[parent].vertices);rows.append({'pair':pair['pair'],'skinTriangle':ti,'nativeCoarseFace':parent,'nativeCoarseVertices':f,'coarseWorldCoordinates':V[f].tolist(),'actualTriangleNormal':n.tolist(),'actualTriangleWorldCoordinates':W[tr].tolist(),'witnessPoints':hit['worldIntersectionOrTouchPointsM']})
 out={'source':str(SRC),'existingCappedWitnessesReusedWithoutRerunningContact':True,'actualSourceSkinVertices':len(V),'actualSourceSkinFaces':len(raw.data.polygons),'witnesses':rows,'uniqueNativeFaces':sorted({r['nativeCoarseFace'] for r in rows}),'seconds':time.time()-tick};(E/'actual-native-orbital-contact-faces.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('R120_ACTUAL_NATIVE_ORBITAL_FACES',len(rows),out['uniqueNativeFaces'],'normalsY',np.quantile([r['actualTriangleNormal'][1] for r in rows],[0,.5,1]).tolist(),flush=True)
if __name__=='__main__':main()
