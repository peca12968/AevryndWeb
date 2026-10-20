"""One complete-woman scalp-bound native fibre pilot; cheap static preview first."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0093-surface-bound-direct-rods';S=R/'engine/assets/characters/female-next/source'
SRC=S/'aevrynd-female-next-r0092-a-native-Eve-groom.blend';OUT=S/'aevrynd-female-next-r0093-a-surface-bound-chain-pilot.blend'
def mod(n,p):
 sp=importlib.util.spec_from_file_location(n,p);a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
v=mod('r93views',Path(__file__).with_name('render-female-next-r0091-matched.py'));v.E=E;m=v.m;q=m.q
eng=mod('r93solver',R/'engine/character/physics/groom_direct_chain_study.py')
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

class RefreshedBody:
 def __init__(self,V,T,radius):
  self.tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);self.radius=radius.reshape(-1);self.position=None;self.distance=None;self.signed=None;self.queries=0;self.corrections=0;self.maxCorrection=0.
 def __call__(self,X):
  P=X.reshape(-1,3)
  if self.position is None:ix=np.arange(len(P));self.position=P.copy();self.distance=np.zeros(len(P));self.signed=np.zeros(len(P))
  else:
   travel=np.linalg.norm(P-self.position,axis=1)
   ix=np.flatnonzero((self.distance-travel<self.radius+.0005)|(self.signed<0))
  # Nearest outward supporting planes are RESPONSE only, never an inside test.
  for i in ix:
   pt,no,face,d=self.tree.find_nearest(Vector(P[i]));N=np.array(no);signed=float(np.dot(P[i]-np.array(pt),N));self.position[i]=P[i];self.distance[i]=d;self.signed[i]=signed;self.queries+=1
   if i%X.shape[1] and signed<self.radius[i]:
    move=self.radius[i]-signed;P[i]+=move*N;self.corrections+=1;self.maxCorrection=max(self.maxCorrection,move)

def main():
 tick=time.time();assert not OUT.exists();assert sha(SRC)=='42cec33c08b4b5f061ad408c3c8f1cf0586d7c4002d3f27c6dfbf6b0f26683f5'
 bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects['AFN92_NATIVE_EVE_RENDER_FIBRES'];A=np.array(o.matrix_world);raw=q.hair(o).reshape(-1,33,3).astype('f8');assert raw.shape==(28002,33,3)
 # New equal-material representation is the ACTUAL displayed curve, never
 # transferred as offsets back onto the nonuniform source CVs (r70C failure).
 P=np.empty_like(raw);sourceArc=np.zeros(raw.shape[:2]);jmap=np.empty(raw.shape[:2],'i4');amap=np.empty(raw.shape[:2])
 for i,row in enumerate(raw):
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(row,axis=0),axis=1))];assert np.all(np.diff(arc)>1e-9)
  u=np.linspace(0,arc[-1],33);j=np.minimum(np.searchsorted(arc,u,side='right')-1,31);a=(u-arc[j])/(arc[j+1]-arc[j]);P[i]=row[j]*(1-a[:,None])+row[j+1]*a[:,None];jmap[i]=j;amap[i]=a;sourceArc[i]=arc
 body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);V,T=body['V'],body['T'];head=np.load(R/'Evidence/character-female-next/r0090-native-scalp-groom/actual-head-surface.npz');assert np.max(abs(V[head['bodyVertexIDs']]-head['world']))<1e-7
 ht=T[head['bodyTriangleIDs']];tree=BVHTree.FromPolygons(V.tolist(),ht.tolist(),all_triangles=True);rad=q.arr(o.data.attributes['radius'].data,'value',raw.size//3).reshape(-1,33)*np.linalg.norm(A[:3,0]);rootTri=np.empty(len(P),'i4');bary=np.empty((len(P),3));normal=np.empty((len(P),3));roots=np.empty((len(P),3))
 for i,root in enumerate(P[:,0]):
  pt,no,f,d=tree.find_nearest(Vector(root));rootTri[i]=head['bodyTriangleIDs'][f];tri=V[ht[f]];bary[i]=m.rig.base.bary(np.array(pt),tri);normal[i]=no;roots[i]=np.array(pt)+np.array(no)*rad[i,0]
 # Surface exit reconstruction changes root only. All free nodes are then
 # solved as one compliant chain against the actual current body surface.
 rootDelta=roots-P[:,0];P[:,0]=roots;solver=eng.DirectChains(P,rad);contact=RefreshedBody(V,T,rad);rows=[]
 for step in range(8):
  row=solver.advance(roots,solver.curvature,contact);row.update(substep=step+1,seconds=time.time()-tick,bodyQueries=contact.queries,pointResponseCorrections=contact.corrections);rows.append(row);save('a-static-solver.json',{'rows':rows,'scope':'Uncalibrated discrete point supporting-plane body response, no self/finite-shaft/CCD/render certificate.'});print('R93_STATIC',row,flush=True)
  if row['maximumRelativeEdgeStrain']>.10 or not np.isfinite(solver.x).all():break
 local=(solver.x.reshape(-1,3)-A[:3,3])@np.linalg.inv(A[:3,:3]).T;d=o.data.copy();d.name='AFN93_ACTUAL_EQUAL_MATERIAL_FIBRES';d.position_data.foreach_set('vector',local.astype('f4').ravel());o.data=d;o.name='AFN93_SURFACE_BOUND_RENDER_FIBRES';o['scope']='All28002 actual native POLY strands,33 equal-material points; all source/root IDs preserved. Actual evaluated scalp triangle+barycentric radius-offset surface-exit root binding and simultaneous full-chain stretch/vector bend, refreshed actual body response. Static unaccepted pilot; no self, shaft, CCD, natural motion, runtime qualification.'
 np.savez_compressed(E/'a-binding-and-chain-lineage.npz',sourceWorld=raw.astype('f4'),sourceArc=sourceArc.astype('f4'),materialMapJ=jmap,materialMapWeight=amap.astype('f4'),rootTriangle=rootTri,rootBarycentric=bary,rootNormal=normal,roots=roots,rootDelta=rootDelta,rest=solver.rest.astype('f4'),actualWorld=solver.x.astype('f4'),worldRadius=rad.astype('f4'),objectMatrix=A,bodyV=V.astype('f4'),bodyT=T)
 bpy.context.view_layer.update();m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'bytes':OUT.stat().st_size,'curves':len(P),'pointsEach':33,'rows':rows,'rootWorldShiftQuantilesM':np.quantile(np.linalg.norm(rootDelta,axis=1),[0,.5,.95,1]),'bodyQueries':contact.queries,'pointResponseCorrections':contact.corrections,'maximumPointResponseCorrectionM':contact.maxCorrection,'method':'Own simultaneous direct full-chain stretch Newton and vector-curvature banded solve; actual current body response queried afresh for near/previous-inside points. No frozen planes, no FTL, no original nonuniform-CV offset transfer.','primaryPrincipleReference':'https://www.animation.rwth-aachen.de/publication/0557/','notPaperCosseratTwistImplementation':True,'youngPa':3e9,'densityKgM3':1300,'dt':solver.dt,'substeps':len(rows),'materialCalibrationAccepted':False,'noRootsStrandsDeletedAndRadiiUnchanged':True,'allFinite':bool(np.isfinite(solver.x).all()),'contactNaturalDynamicsRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 controls=[]
 for view in ['face','back','body-face']:controls.append(v.image('a-bound-chain',view));save('a-view-controls.json',controls)
 print('R93_ACTUAL_COMPLETE_PILOT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
