"""Author replacement outer-lid quad rows between actual shared boundaries.
Existing source outer Skin supplies rest surface/UV and cross-section curvature.
No posterior-only lining, auto Boolean subdivision, external closing plate or
unconstrained correction of unchanged topology is used.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0157-outer-lid-retopology'
sp=importlib.util.spec_from_file_location('r157author',Path(__file__).with_name('build-female-next-r0155-margin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else str(x))+'\n').encode())
def ordered(ids,V):
 ids=list(map(int,ids));left=int(np.argmin(V[ids,0]));ids=ids[left:]+ids[:left];right=int(np.argmax(V[ids,0]));p=ids[:right+1];q=[ids[0]]+list(reversed(ids[right:]));up,low=(p,q) if V[p,2].mean()>V[q,2].mean() else (q,p);out=up+list(reversed(low[1:-1]));nup=len(up);parameter=np.empty(len(out));upper=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(V[up],axis=0),axis=1))];lower=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(V[low],axis=0),axis=1))];parameter[:nup]=.5*upper/upper[-1];parameter[nup:]=1-.5*lower[1:-1][::-1]/lower[-1];return np.array(out,'i4'),parameter
def interpolate(ids,t,at,V):return np.stack([np.interp(at,np.r_[t,1.],np.r_[V[ids,k],V[ids[0],k]]) for k in range(3)],axis=1)
def frames(span,tangent):
 x=span/np.maximum(np.linalg.norm(span,axis=1)[:,None],1e-30);z=np.cross(tangent,x);z/=np.maximum(np.linalg.norm(z,axis=1)[:,None],1e-30);y=np.cross(z,x);return np.stack([x,y,z],axis=2)
def main():
 tick=time.time();b=json.loads((E.parent/'r0155-native-blink/b-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];V,T=a.geometry(skin);d=skin.data;d.calc_loop_triangles();poly=np.array([t.polygon_index for t in d.loop_triangles]);uv=d.uv_layers.active;sourceUV=np.array([tuple(q.uv) for q in uv.data]);report=json.loads((E/'actual-outer-lid-boundaries.json').read_text());arrays=np.load(E/'actual-outer-lid-boundaries.npz');s.frame_set(11);bpy.context.view_layer.update();closed=a.geometry(skin)[0];s.frame_set(1);bpy.context.view_layer.update();points=[];sourceTri=[];bcs=[];tex=[];corrections=[];sideIds=[];boundaryFlags=[];faces=[];replaced=[];boundaryOld=[];roles=[];rows=[]
 for si,side in enumerate(['L','R']):
  row=next(x for x in report['reports'] if x['side']==side);assert not row['branchedBoundaryDegrees'] and len(row['loops'])==2;innerLoop=next(x for x in row['loops'] if 'AFN57_CANONICAL_IRIS' in x['adjacentUnselectedMaterials']);outerLoop=next(x for x in row['loops'] if 'AFN126_NATIVE_ARTIST_HEAD_MATERIAL' in x['adjacentUnselectedMaterials']);inner,t=ordered(innerLoop['originalVertexIds'],V);outer,to=ordered(outerLoop['originalVertexIds'],V);N=len(inner);M=len(outer);O=interpolate(outer,to,t,V);OC=interpolate(outer,to,t,closed);I=V[inner];IC=closed[inner];tangent=np.roll(I,-1,axis=0)-np.roll(I,1,axis=0);tangentC=np.roll(IC,-1,axis=0)-np.roll(IC,1,axis=0);restFrame=frames(O-I,tangent);newFrame=frames(OC-IC,tangentC);ratio=np.linalg.norm(OC-IC,axis=1)/np.maximum(np.linalg.norm(O-I,axis=1),1e-12);selected=arrays[side+'-selectedPolygons'];replaced.extend(selected.tolist());triIds=np.flatnonzero(np.isin(poly,selected));tree=BVHTree.FromPolygons([Vector(p) for p in V],T[triIds].tolist(),all_triangles=True);base=len(points);rValues=[0.,.16,.33,.52,.70,.86];worst=0.
  for j,r in enumerate(rValues):
   guess=(1-r)*I+r*O
   for k,p in enumerate(guess):
    if j==0:
     tri=np.array([inner[k]]*3);bc=np.array([1.,0.,0.]);P=V[inner[k]];uvtri=next(triIdx for triIdx in triIds if inner[k] in T[triIdx]);looptri=d.loop_triangles[int(uvtri)];corner=list(T[uvtri]).index(inner[k]);uvp=sourceUV[looptri.loops[corner]];Q=closed[inner[k]]
    else:
     hit=tree.find_nearest(Vector(p));triIdx=int(triIds[int(hit[2])]);tri=T[triIdx];P,bc=h.h.actual_triangle_anchor(p,V[tri]);uvp=bc@sourceUV[list(d.loop_triangles[triIdx].loops)];linear=(1-r)*I[k]+r*O[k];bend=P-linear;local=restFrame[k].T@bend;Q=(1-r)*IC[k]+r*OC[k]+newFrame[k]@(local*ratio[k]);worst=max(worst,float(np.linalg.norm(P-p)))
    baseClosed=bc@closed[tri];points.append(P);sourceTri.append(tri);bcs.append(bc);tex.append(uvp);corrections.append(Q-baseClosed);sideIds.append(si);boundaryFlags.append(j==0);roles.append(j)
  for k,vi in enumerate(outer):
   triIdx=next(triIdx for triIdx in triIds if vi in T[triIdx]);looptri=d.loop_triangles[int(triIdx)];corner=list(T[triIdx]).index(vi);points.append(V[vi]);sourceTri.append([vi]*3);bcs.append([1.,0.,0.]);tex.append(sourceUV[looptri.loops[corner]]);corrections.append([0.,0.,0.]);sideIds.append(si);boundaryFlags.append(True);roles.append(6)
  for j in range(len(rValues)-1):
   for k in range(N):faces.append([base+j*N+k,base+j*N+(k+1)%N,base+(j+1)*N+(k+1)%N,base+(j+1)*N+k])
  ii=jj=0;last=base+(len(rValues)-1)*N;outBase=base+len(rValues)*N
  while ii<N or jj<M:
   ti=t[ii+1] if ii+1<N else 1.;tj=to[jj+1] if jj+1<M else 1.
   if ii<N and (jj>=M or ti<=tj):faces.append([last+ii%N,last+(ii+1)%N,outBase+jj%M]);ii+=1
   else:faces.append([last+ii%N,outBase+(jj+1)%M,outBase+jj%M]);jj+=1
  boundaryOld.extend(inner.tolist()+outer.tolist());rows.append({'side':side,'sourceOuterPolygonsReplacedCompletely':len(selected),'trueInnerBoundaryVertices':N,'trueOuterBoundaryVertices':M,'editableCrossSectionRows':rValues,'maximumRestProjectionToOriginalArtistSkinM':worst,'closedToRestCrossSectionLengthRatioRange':[float(ratio.min()),float(ratio.max())]})
 P=np.array(points);F=[]
 for face in faces:
  a0,a1,a2=P[face[:3]];normal=np.cross(a1-a0,a2-a0);side=sideIds[face[0]];C=np.array([.029 if side==0 else -.029,-.1033,1.4632]);rad=P[face].mean(0)-C
  if np.dot(normal,rad)<0:face=list(reversed(face))
  F.append(face)
 mesh=bpy.data.meshes.new('AFN157_AUTHORED_OUTER_LID_RIM_TURN_CREASE');mesh.from_pydata(P.tolist(),[],F);mesh.update();ob=bpy.data.objects.new('AFN157_ACTUAL_EDITABLE_OUTER_LIDS',mesh);s.collection.objects.link(ob)
 for mat in d.materials:mesh.materials.append(mat)
 for p in mesh.polygons:p.material_index=report['artistOuterMaterialId'];p.use_smooth=True
 uvnew=mesh.uv_layers.new(name=uv.name);uvnew.data.foreach_set('uv',np.array([tex[i] for f in F for i in f],dtype='f4').ravel());mesh.calc_loop_triangles();TT=np.array([tuple(t.vertices) for t in mesh.loop_triangles]);areas=np.linalg.norm(np.cross(P[TT[:,1]]-P[TT[:,0]],P[TT[:,2]]-P[TT[:,0]]),axis=1);save('direct-outer-lid-topology-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T09:07:06+00:00','actualNativeMeshCreated':ob.name,'actualVertices':len(P),'actualPolygons':len(F),'actualTriangles':len(TT),'zeroAreaTriangles':int((areas==0).sum()),'changedPremise':'Replace whole visible source outer lid bands using true shared boundary loops and editable rim/turn/crease rows. Original source rest skin/UV and measured cross-section curvature define the new closed tissue patch; no auto Boolean subdivision/posterior-only patch or cap overlay. Actual patch joins complete Skin and is not a preview proxy.','sourceRole':'Unaccepted authored component; not a complete woman until integration and actual full previews.','normalOrientationScope':'Original native eye-centre neighbourhood radial orientation used for local external skin only; not anatomical/contact acceptance.'});assert (areas>0).all(),'Actual authored outer-lid topology is degenerate'
 np.savez_compressed(E/'authored-outer-lid-patch.npz',positions=P,faceCounts=np.array([len(f) for f in F],'i4'),faceIndices=np.array([i for f in F for i in f],'i4'),uvPerVertex=np.array(tex),sourceVertices=np.array(sourceTri,'i4'),barycentric=np.array(bcs),closedCorrection=np.array(corrections),side=np.array(sideIds,'i4'),boundary=np.array(boundaryFlags),role=np.array(roles,'i4'),replacedPolygons=np.array(replaced,'i4'),originalBoundaryVertices=np.array(boundaryOld,'i4'));save('authored-outer-lid-construction.json',{'source':b,'actualMesh':ob.name,'eyes':rows,'actualVertices':len(P),'actualFaces':len(F),'actualTriangles':len(TT),'zeroAreaRestTriangles':int((areas==0).sum()),'minimumTwiceTriangleAreaM2':float(areas.min()),'sourceBodyAndOtherMeshesNotEdited':True,'sourceUVInterpolatedFromActualArtistOuterSkin':True,'newClosedFormNotPhysiologyOrContactProof':True});print('R157_ACTUAL_NATIVE_OUTER_LID_PATCH_AUTHORED',len(P),len(F),time.time()-tick,flush=True)
if __name__=='__main__':main()
