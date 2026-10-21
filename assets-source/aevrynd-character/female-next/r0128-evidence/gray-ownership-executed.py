"""Map actual r127 gray-band ray triangles to exact native socket ownership."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0128-finite-native-lid-walls';PRE=E.parent/'r0127-native-lid-closure'
sp=importlib.util.spec_from_file_location('r128own',Path(__file__).with_name('build-female-next-r0127-native-lid-closure.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def main():
 build=json.loads((PRE/'a-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=build['output']);a.deliver(1.);skin=bpy.data.objects[build['actualDisplayedSkin']];d,W,T=a.b.u.b.geom(skin);line=np.load(PRE/'native-lid-authoring-lineage.npz');P=line['sourceHead'];ST=line['sourceTriangles'];ids=line['actualNativeCorrespondence'];lookup={tuple(sorted(t)):i for i,t in enumerate(ST)};dom=np.load(E/'actual-native-lid-domains.npz');inside=set(np.r_[dom['L_socketFaces'],dom['R_socketFaces']]);rays=json.loads((PRE/'minimum-saved-native-lid-readback.json').read_text())['actualGrayBandDiagnosticRays'];rows=[]
 for r in rays:
  hit=next((h for h in r['hitsFrontToBack'] if h['object']==skin.name),None)
  if hit is None:continue
  ti=hit['triangle'];native=ids[T[ti]];fi=lookup.get(tuple(sorted(native)));A=P[ST[fi]] if fi is not None else None;N=W[T[ti]];row={'pixel':r['pixel'],'actualSkinTriangle':ti,'sourceTriangle':fi,'sourceDomain':'closed socket wall' if fi in inside else 'retained outer skin','nativeVertexIds':native.tolist(),'actualSkinWasFirstRawSurface':r['hitsFrontToBack'][0]['object']==skin.name}
  if A is not None:
   n=np.cross(A[1]-A[0],A[2]-A[0]);m=np.cross(N[1]-N[0],N[2]-N[0]);row.update(sourceNormal=(n/np.linalg.norm(n)).tolist(),deformedNormal=(m/np.linalg.norm(m)).tolist(),actualAreaRatio=float(np.linalg.norm(m)/np.linalg.norm(n)))
  rows.append(row)
 a.save if False else None
 (E/'gray-band-actual-native-ownership.json').write_text(json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sampledActualGrayBandRays':rows,'actualClosedSocketFaceCount':len(inside),'scope':'Exact source-face ownership and raw surface rays only; not full material/render occupancy proof.'},indent=2)+'\n',encoding='utf-8');print('R128_GRAY_NATIVE_OWNERSHIP_DONE',[(r['pixel'],r['sourceDomain']) for r in rows],flush=True)
if __name__=='__main__':main()
