"""Third/final neck construction: actual source section secants + valid UV charts.
Keep promising full artist face and original body. No normal-weight/ring sweep.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,importlib.util,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0126-individual-head-foundation';SRC=S/'r0126-source/aevrynd-female-next-r0126-a2-source-material-neck.blend';OUT=S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'
sp=importlib.util.spec_from_file_location('r126sections',Path(__file__).with_name('build-female-next-r0126-individual-head.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def source_data(ob,z0,z1):
 d,W,T=b.u.b.geom(ob);W=W.copy();T=T.copy();loops=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');uv={layer.name:q.arr(layer.data,'uv',len(d.loops),2)[loops].copy() for layer in d.uv_layers};centers=W[T].mean(1);selected=np.flatnonzero((centers[:,2]>z0-.012)&(centers[:,2]<z1+.008));tree=BVHTree.FromPolygons(W.tolist(),T[selected].tolist(),all_triangles=True);return W,T,uv,selected,tree
def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def source_section(W,T,z,center,angles):
 P=W[T];P=P[(P[:,:,2].min(1)<z)&(P[:,:,2].max(1)>z)];segments=[]
 for tri in P:
  hits=[]
  for u,v in zip(tri,np.roll(tri,-1,axis=0)):
   if (u[2]<z)!=(v[2]<z):hits.append((u+(v-u)*((z-u[2])/(v[2]-u[2])))[:2])
  if len(hits)==2:segments.append(hits)
 segments=np.array(segments);A=segments[:,0]-center;edge=segments[:,1]-segments[:,0];out=[]
 for theta in angles:
  direction=np.array([math.cos(theta),math.sin(theta)]);den=cross2(direction,edge);valid=abs(den)>1e-12;t=np.full(len(den),np.nan);u=t.copy();t[valid]=cross2(A[valid],edge[valid])/den[valid];u[valid]=cross2(A[valid],direction)/den[valid];hits=np.sort(t[valid&(t>0)&(u>=-1e-9)&(u<=1+1e-9)]);assert len(hits)>0
  assert hits[-1]-hits[0]<2e-6,('non-star or multiple section at same ray',z,theta,hits);out.append([center[0]+hits.mean()*direction[0],center[1]+hits.mean()*direction[1],z])
 return np.array(out)
def face_uv(points,source,layerNames):
 W,T,uv,selected,tree=source;co,no,face,distance=tree.find_nearest(Vector(points.mean(0)));assert face is not None;f=int(selected[face]);tri=W[T[f]];U=tri[1]-tri[0];V=tri[2]-tri[0];AA=np.dot(U,U);AB=np.dot(U,V);BB=np.dot(V,V);den=AA*BB-AB*AB;assert den>1e-20;rel=points-tri[0];x=(BB*(rel@U)-AB*(rel@V))/den;y=(AA*(rel@V)-AB*(rel@U))/den;weights=np.column_stack((1-x-y,x,y));return {name:weights@uv[name][f] for name in layerNames},float(distance),f
def main():
 tick=time.time();assert not OUT.exists();build=json.loads((E/'a2-build-summary.json').read_text('utf-8'));assert a.a.sha(SRC)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0.);skin=bpy.data.objects[build['actualSkinObject']];native=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];artist=bpy.data.objects[build['sourceHeadObject']];z0=build['bodyCutWorldZ'];z1=build['headCutWorldZ'];dz=z1-z0;nativeData=source_data(native,z0,z1);artistData=source_data(artist,z0,z1);lineage=np.load(E/'individual-head-neck-lineage.npz');original=lineage['bridgePoints'].reshape(5,-1,3);angles=lineage['sharedAngles'];C0=lineage['bodyPlaneCenter'];C1=lineage['headPlaneCenter'];step=.002;below=source_section(nativeData[0],nativeData[1],z0-step,C0,angles);above=source_section(artistData[0],artistData[1],z1+step,C1,angles);T0=(original[0]-below)/step;T1=(above-original[-1])/step
 bm=bmesh.new();bm.from_mesh(skin.data);patchIndex=next(i for i,m in enumerate(skin.data.materials) if m and m.name=='AFN126_EXACT_DUAL_SOURCE_NECK_MATERIAL');oldFaces=[f for f in bm.faces if f.material_index==patchIndex];oldUV=next(layer for layer in bm.loops.layers.uv.values() if layer.name=='AngelicaOriginalUV');oldArea=[]
 for f in oldFaces:
  P=np.array([loop[oldUV].uv[:] for loop in f.loops]);oldArea.append(abs(np.sum(cross2(P,np.roll(P,-1,axis=0))))*.5)
 bmesh.ops.delete(bm,geom=oldFaces,context='FACES');loose=[v for v in bm.verts if not v.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
 L,LA,_=a.ring(bm,z0,C0);H,HA,_=a.ring(bm,z1,C1);assert len(L)==len(H)==len(angles) and max(abs(LA-angles).max(),abs(HA-angles).max())<3e-5;P0=np.array([v.co[:] for v in L]);P1=np.array([v.co[:] for v in H]);rings=[L];positions=[P0];intervals=16
 for j in range(1,intervals):
  t=j/intervals;P=(2*t**3-3*t*t+1)*P0+(t**3-2*t*t+t)*dz*T0+(-2*t**3+3*t*t)*P1+(t**3-t*t)*dz*T1;assert np.isfinite(P).all() and abs(P[:,2]-(z0+dz*t)).max()<3e-7;rings.append([bm.verts.new(p) for p in P]);positions.append(P)
 rings.append(H);positions.append(P1);blend=bm.verts.layers.float.get('AFN126_NECK_BLEND');nativeWeight=bm.verts.layers.float.get('AFN113_NATIVE_COLOR_WEIGHT');assert blend and nativeWeight;layers={layer.name:layer for layer in bm.loops.layers.uv.values()};nativeNames=[name for name in layers if name!='AngelicaOriginalUV'];assert all(name in nativeData[2] for name in nativeNames);headName=next(iter(artistData[2]));newArea=[];distances=[];sourceFaces=[];newFaces=[]
 for j,row in enumerate(rings):
  t=j/intervals
  for v in row:v[blend]=t*t*(3-2*t);v[nativeWeight]=1.
 for j in range(intervals):
  for i in range(len(angles)):
   k=(i+1)%len(angles);verts=[rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]];points=np.array([v.co[:] for v in verts]);bodyUV,db,fb=face_uv(points,nativeData,nativeNames);headUV,dh,fh=face_uv(points,artistData,[headName]);f=bm.faces.new(verts);f.material_index=patchIndex;f.smooth=True;newFaces.append(f)
   for h,loop in enumerate(f.loops):
    for name in nativeNames:loop[layers[name]].uv=bodyUV[name][h]
    loop[layers['AngelicaOriginalUV']].uv=headUV[headName][h]
   UV=headUV[headName];newArea.append(abs(np.sum(cross2(UV,np.roll(UV,-1,axis=0))))*.5);distances.append([db,dh]);sourceFaces.append([fb,fh])
 bmesh.ops.recalc_face_normals(bm,faces=newFaces);assert all(len(bm.edges.get((row[i],row[(i+1)%len(row)])).link_faces)==2 for row in [L,H] for i in range(len(row)));bm.to_mesh(skin.data);bm.free();skin.data.update();bpy.context.view_layer.update();_,W,T=b.u.b.geom(skin);assert np.isfinite(W).all();np.savez_compressed(E/'source-section-neck-lineage.npz',originalRuledRings=original,sourceBelowSection=below,sourceAboveSection=above,sourceDzTangents=np.array([T0,T1]),newSectionRings=np.array(positions),oldArtistUVQuadAreas=np.array(oldArea),newArtistUVQuadAreas=np.array(newArea),sourceUVFaceIDs=np.array(sourceFaces),sourceUVNearestFaceCentroidDistancesM=np.array(distances));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);a.save('b-build-summary.json',build|{'source':str(SRC),'sourceSha256':a.a.sha(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'repair':'Third/final fixed source-section neck construction. Actual2mm adjacent source cross-sections define dz secants; reconstruct16 neck intervals. Actual original native-body/artist-neck triangle UV chart derivatives populate every junction face, replacing height-degenerate constant UVs. No source head/body warp, shader/scalar/light change or parameter sweep.','actualVertices':len(W),'actualTriangles':len(T),'actualGeometryAndTrianglesExactlyPreserved':False,'correctedNeckFaces':len(newFaces),'geometryPreservationScope':'Original body/head outside reconstructed neck retained; neck topology and UVs rebuilt, not whole-skin equality.','neckBridgeQuads':len(newFaces),'oldArtistUVFacesAtOrBelow1eMinus14Area':int((np.array(oldArea)<=1e-14).sum()),'newArtistUVFacesAtOrBelow1eMinus14Area':int((np.array(newArea)<=1e-14).sum()),'newArtistUVQuadAreaQuantiles':np.quantile(newArea,[0,.5,.95,1]),'sourceSectionDifferenceStepM':step,'allSourceContoursAndUVDataPreserved':True,'sourceGeometryUVSamplingNotHeadEnvelopeProjection':True,'allNeckInterfaceEdgesHaveTwoIncidentFaces':True,'sourceSecantsAndStaticSamplingNotExactRenderedG1OrFiniteContinuousContactProof':True,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','body-face','profile','oblique','back']:
  rows.append(b.u.v.image('b-source-section-neck',view));a.save('b-view-controls.json',rows)
 print('R126_COMPLETE_SOURCE_SECTION_NECK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
