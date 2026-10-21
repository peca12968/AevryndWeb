"""Independent actual retained lower-body and original head surface identity.
Point/triangle preservation is not finite contact, animation or anatomy proof.
"""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0126-individual-head-foundation'
sp=importlib.util.spec_from_file_location('r126retain',Path(__file__).with_name('build-female-next-r0126-individual-head.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b
def canonical(t):
 i=int(np.argmin(t));return tuple(int(v) for v in np.roll(t,-i))
def main():
 tick=time.time();build=json.loads((E/'b-build-summary.json').read_text('utf-8'));p=Path(build['output']);assert a.a.sha(p)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));b.deliver(0.);skin=bpy.data.objects[build['actualSkinObject']];_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();tree=KDTree(len(W))
 for i,v in enumerate(W):tree.insert(Vector(v),i)
 tree.balance();out={}
 for role,name,z,lower in [('nativeLowerBody','AFN113_COMPLETE_WOMAN_COHERENT_HEAD',build['bodyCutWorldZ'],True),('originalArtistHeadAboveNeck',build['sourceHeadObject'],build['headCutWorldZ'],False)]:
  _,V,F=b.u.b.geom(bpy.data.objects[name]);V=V.copy();F=F.copy();mask=(V[:,2]<z-1e-6) if lower else (V[:,2]>z+1e-6);ids=np.flatnonzero(mask);mapping=np.full(len(V),-1,dtype='i4');distances=[]
  for i in ids:
   co,j,distance=tree.find(Vector(V[i]));mapping[i]=j;distances.append(distance)
  maximum=float(max(distances));assert maximum<3e-7,(role,maximum);expected={canonical(mapping[f]) for f in F[np.all(mask[F],axis=1)]};wm=(W[:,2]<z-1e-6) if lower else (W[:,2]>z+1e-6);actual={canonical(t) for t in T[np.all(wm[T],axis=1)]};missing=expected-actual;added=actual-expected
  out[role]={'sourceObject':name,'verticesCompared':len(ids),'maximumWorldPointDifferenceM':maximum,'originalOrientedTriangles':len(expected),'actualOrientedTriangles':len(actual),'missingOrientedTriangles':len(missing),'addedOrientedTriangles':len(added),'exactOrientedTriangleCorrespondence':not missing and not added};assert not missing and not added,(role,len(missing),len(added))
 assert a.a.sha(p)==build['sha256'];a.save('actual-surface-retention.json',{'candidate':str(p),'sha256':build['sha256'],'regions':out,'scope':'Actual displayed source coordinates and oriented triangles outside the reconstructed neck retained within float world readback precision. Not global nearest surface fitting, source shape warp, complete anatomy/operation/finite-self-continuous-contact/runtime proof.','seconds':time.time()-tick});print('R126_ACTUAL_BODY_AND_ARTIST_HEAD_SURFACE_RETENTION_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
