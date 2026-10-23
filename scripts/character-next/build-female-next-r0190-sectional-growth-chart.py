"""Current anatomical section chart: one whole coarse growth form first.

Sections are cut from actual Skin triangles, not UVs or a geodesic gradient.
An authored anterior part and posterior fan define the comb chart. All tails
are rebuilt; no previous failed groom or free paths are transferred.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0190-sectional-growth-chart';OUT=C/'assets-source/aevrynd-character/female-next/r0190-source/aevrynd-female-next-r0190-coarse-sectional-growth.blend'
sp=importlib.util.spec_from_file_location('r190base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def section(B,normal,anchor,direction):
 signed=(B-anchor)@normal;cross=(signed.min(1)<=0)&(signed.max(1)>0);pairs=[]
 for idx in np.flatnonzero(cross):
  pts=[]
  for j,k in [(0,1),(1,2),(2,0)]:
   x,y=signed[idx,j],signed[idx,k]
   if (x<=0<y) or (y<=0<x):pts.append(B[idx,j]+x/(x-y)*(B[idx,k]-B[idx,j]))
  if len(pts)!=2:continue
  u,v=pts;du=float((u-anchor)@direction);dv=float((v-anchor)@direction)
  if max(du,dv)<0:continue
  if du<0:u=u+(-du)/(dv-du)*(v-u)
  elif dv<0:v=v+(-dv)/(du-dv)*(u-v)
  if np.linalg.norm(u-v)>1e-7:pairs.append((u,v))
 if not pairs:return []
 nodes=[];lookup={};adj={}
 for u,v in pairs:
  ij=[]
  for p in [u,v]:
   key=tuple(np.round(p/1e-6).astype('i8'))
   if key not in lookup:lookup[key]=len(nodes);nodes.append(p)
   ij.append(lookup[key])
  i,j=ij;adj.setdefault(i,set()).add(j);adj.setdefault(j,set()).add(i)
 nodes=np.array(nodes);remaining=set(adj);chains=[]
 while remaining:
  component=set();todo=[next(iter(remaining))]
  while todo:
   k=todo.pop()
   if k in component:continue
   component.add(k);todo.extend(adj[k]-component)
  remaining-=component;ends=[i for i in component if len(adj[i])==1];start=max(ends or component,key=lambda i:nodes[i,2]);order=[start];seen={start}
  while True:
   candidates=adj[order[-1]]-seen
   if not candidates:break
   nxt=max(candidates,key=lambda i:nodes[i,2]);order.append(nxt);seen.add(nxt)
  p=nodes[order]
  if len(p)<3:continue
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
  if arc[-1]<.003:continue
  if p[0,2]<p[-1,2]:p=p[::-1];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
  chains.append((p,arc))
 return chains
def resample(points,arc,t):return np.column_stack([np.interp(t,arc,points[:,j]) for j in range(3)])
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);s.camera.data.type='PERSP'
 skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];old=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];old.material_slots[0].link='DATA';old.hide_render=True;old.hide_set(True)
 for n,hide in [('AFN184_ACTUAL_NATIVE_DEFORMED_LASHES',True),('AFN126_ORIGINAL_Eyelashes_Eyelashes_0',False)]:bpy.data.objects[n].hide_render=hide;bpy.data.objects[n].hide_set(hide)
 bpy.context.view_layer.update();protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);sf=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz')['actualScalpFaces'];tri=T[sf];B=W[tri];cross=np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]);area=np.linalg.norm(cross,axis=1)/2;norm=cross/(2*area[:,None]);tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True)
 pivot=.005;ys=np.linspace(float(B[:,:,1].min())+1e-5,pivot,64);angles=np.linspace(0,math.pi,97);chart=[];chartMeta=[]
 for side in [-1,1]:
  for y in ys:
   anchor=np.array([0,y,0.]);direction=np.array([side,0.,0.]);chains=section(B,np.array([0.,1.,0.]),anchor,direction);chart.append(chains);chartMeta.append(('side',side,float(y),direction))
 for angle in angles:
  direction=np.array([math.cos(angle),math.sin(angle),0.]);chains=section(B,np.array([-direction[1],direction[0],0]),np.array([0.,pivot,0.]),direction);chart.append(chains);chartMeta.append(('back',0,float(angle),direction))
 # Complete two-dimensional area-distributed births, retaining every sampled root.
 N=4096;K=49;rng=np.random.default_rng(19061061);faces=rng.choice(len(B),N,p=area/area.sum());u=rng.random(N);v=rng.random(N);rt=np.sqrt(u);bc=np.column_stack([1-rt,rt*(1-v),rt*v]);roots=np.einsum('ni,nij->nj',bc,B[faces]);rootN=norm[faces];P=np.empty((N,K,3),'f4');chartIds=[];chartGaps=[];exitPoints=[];surfaceLength=[];failed=[];allSections=[];sectionOffsets=[0]
 for chains in chart:
  for cp,ar in chains:allSections.extend(cp);sectionOffsets.append(len(allSections))
 for i,r in enumerate(roots):
  if r[1]<=pivot:
   row=int(np.argmin(np.abs(ys-r[1])));ci=row+(64 if r[0]>=0 else 0)
  else:ci=128+int(np.argmin(np.abs(angles-math.atan2(r[1]-pivot,r[0]))))
  chartIds.append(ci);chains=chart[ci]
  if not chains:
   # Explicit failed-domain placeholder retained and reported, never silently dropped.
   failed.append(i);P[i]=r+np.linspace(0,.06,K)[:,None]*np.array([0,0,-1]);chartGaps.append(1.);exitPoints.append(r);surfaceLength.append(0.);continue
  best=None
  for cp,ar in chains:
   A=cp[:-1];D=np.diff(cp,axis=0);f=np.clip(np.einsum('ij,ij->i',r-A,D)/np.maximum(np.einsum('ij,ij->i',D,D),1e-20),0,1);Q=A+f[:,None]*D;j=int(np.argmin(np.linalg.norm(Q-r,axis=1)));gap=float(np.linalg.norm(Q[j]-r));rootArc=float(ar[j]+f[j]*(ar[j+1]-ar[j]));candidate=(gap,cp,ar,rootArc,Q[j])
   if best is None or gap<best[0]:best=candidate
  gap,cp,ar,rootArc,q0=best;chartGaps.append(gap);remaining=max(ar[-1]-rootArc,1e-6);surfaceLength.append(float(remaining));surfaceT=np.linspace(rootArc,ar[-1],25);surface=resample(cp,ar,surfaceT);distance=surfaceT-rootArc;blend=np.exp(-distance/.009);surface+=(r-q0)[None]*blend[:,None]
  sn=[]
  for pos in surface:sn.append(tree.find_nearest(Vector(pos))[1])
  sn=np.array(sn);lift=.00015+(.008+.004*rng.random())*(1-np.exp(-distance/.026));surface+=sn*lift[:,None];surface[0]=r+rootN[i]*.00015
  direction=chartMeta[ci][3];exit=surface[-1];exitPoints.append(exit.copy());tip=exit.copy();tip[:2]+=direction[:2]*(.018+.01*rng.random());tip[2]=1.325+.022*rng.random()+.008*(r[2]<1.47)
  tangent=surface[-1]-surface[-3];tangent/=max(np.linalg.norm(tangent),1e-12);length=max(float(np.linalg.norm(tip-exit)),.02);tangent[2]=min(tangent[2],-.2);tangent/=np.linalg.norm(tangent);v0=tangent*length*.75;v1=np.array([0.,0.,-length*.8]);tt=np.linspace(0,1,26)[1:];tail=(2*tt**3-3*tt**2+1)[:,None]*exit+(tt**3-2*tt**2+tt)[:,None]*v0+(-2*tt**3+3*tt**2)[:,None]*tip+(tt**3-tt**2)[:,None]*v1
  full=np.vstack([surface,tail]);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(full,axis=0),axis=1))];P[i]=resample(full,arc,np.linspace(0,arc[-1],K))
 cu=bpy.data.hair_curves.new('AFN190_CURRENT_ANATOMICAL_SECTION_GROWTH_DATA');cu.add_curves([K]*N);cu.position_data.foreach_set('vector',P.ravel());radius=cu.attributes.new('radius','FLOAT','POINT');rs=np.tile(.00015*np.maximum(1-np.linspace(0,1,K),.03)**.65,N);radius.data.foreach_set('value',rs.astype('f4'));ids=cu.attributes.new('AFN190_PERSISTENT_ROOT_ID','INT','CURVE');ids.data.foreach_set('value',np.arange(N,dtype='i4'));hair=bpy.data.objects.new('AFN190_ACTUAL_COARSE_SECTIONAL_GROWTH',cu);s.collection.objects.link(hair)
 mat=bpy.data.materials.new('AFN190_OWN_NATIVE_HAIR_COARSE_SHAPE_ONLY');mat.use_nodes=True;ns=mat.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='MELANIN';bs.inputs['Melanin'].default_value=.75;bs.inputs['Melanin Redness'].default_value=.15;bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.45;output=ns.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],output.inputs[0]);cu.materials.append(mat);bpy.context.view_layer.update()
 assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};rootError=float(np.linalg.norm(P[:,0]-(roots+rootN*.00015),axis=1).max());np.savez_compressed(E/'sectional-growth-lineage.npz',rootTriangles=tri[faces],rootBC=bc,rootWorld=roots.astype('f4'),rootNormals=rootN.astype('f4'),rootIDs=np.arange(N,dtype='i4'),rootChartIds=np.array(chartIds,'i4'),chartNearestRootGap=np.array(chartGaps,'f4'),currentScalpFaces=sf,sectionPoints=np.asarray(allSections,'f4'),sectionOffsets=np.array(sectionOffsets,'i4'),exitPoints=np.asarray(exitPoints,'f4'),surfaceLengths=np.array(surfaceLength,'f4'))
 save('coarse-construction-summary.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Current anatomical side sections plus posterior section fan, full new surface-to-free-tip paths','changedFailedPremise':'Direct current-Skin cross-sections define a two-dimensional growth chart and path continuation; no scalar metric ridges, foreign guide/free-path transfer, native UV inversion or detached isolated clump lofts. First a complete coarse growth shape, not sparse independent bundles.','actualScalpTriangles':len(sf),'actualScalpAreaM2':float(area.sum()),'sectionPlanes':len(chart),'emptyPlaneCount':sum(not x for x in chart),'fullActualBirthCount':N,'coarseNativeCurves':N,'pointsPerCurve':K,'actualRootReconstructionMaximumM':rootError,'currentRootToOwnSectionGapM':{'median':float(np.median(chartGaps)),'p90':float(np.quantile(chartGaps,.9)),'max':float(max(chartGaps))},'missingChartRootIDs':failed,'allBirthsRetained':True,'sourceScalpPatchIsConstructionDomainNotAcceptedBiologicalFollicleMap':True,'coarseRadiusM':.00015,'coarseNotFinalFineHairOrContactQualification':True,'actualHair':hair.name,'actualSkin':skin.name,'protectedRawMeshUVSignatures':protected,'secondsBeforePreview':time.time()-tick})
 a.b.u.v.E=E
 for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('coarse-sectional-growth',v)
 # Restore a neutral full-head camera without rendering a duplicate image.
 s.camera.data.type='PERSP';s.camera.location=(0,-.68,1.49);s.camera.rotation_euler=(Vector((0,-.008,1.49))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=85
 OUT.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'elapsedJobSeconds':time.time()-tick,'coarseOnly':True,'completeFineCandidates':0,'oneConstructionOneMethod':True,'appearanceOperationContactRuntimeUnaccepted':True});print('R190_ONE_COMPLETE_CURRENT_SECTIONAL_GROWTH_COARSE_SAVED',flush=True)
if __name__=='__main__':main()
