"""Reconstruct full native ocular pose from inspected actual artist external sheet.

Register the visible neutral aperture on both actual meshes; transfer actual
artist sheet motion, rather than guessing a native UV seam closure target.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0109-complete-native-lid-sheet';PRE=E.parent/'r0107-native-coarse-lid-cage'
sp=importlib.util.spec_from_file_location('r109art',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def tree(V,T):return BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
def aperture(skin,eye,eyeV):
 lo=eyeV.min(0);hi=eyeV.max(0);xs=np.linspace(lo[0],hi[0],97);zs=np.linspace(lo[2],hi[2],97);rows=[];front=lo[1]-.05
 for x in xs:
  visible=[]
  for z in zs:
   p=Vector((x,front,z));a,_,_,ad=eye.ray_cast(p,Vector((0,1,0)));b,_,_,bd=skin.ray_cast(p,Vector((0,1,0)))
   if a is not None and (b is None or bd>ad):visible.append(z)
  if visible:rows.append((x,min(visible),max(visible)))
 rows=np.array(rows);assert len(rows)>12;return rows
def main():
 tick=time.time();save('sheet-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct full ocular native pose reconstruction from actual registered artist external sheet; no analytic aperture target or hood solver.'});native=np.load(PRE/'native-coarse-lid-poses-pinned.npz');P=native['neutralFineWorld'];T=native['fineTriangles'];artist=np.load(E/'actual-artist-external-blink.npz');A=artist['neutralWorld'];AT=artist['neutralTriangles'];assert np.array_equal(AT,artist['closedTriangles']) and np.array_equal(AT,artist['halfTriangles']);fullnative=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');opt=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];C=np.mean([r['posteriorSphereFitCentreWorld'] for r in opt.values()],0);scale=np.linalg.norm(np.array(opt['L']['posteriorSphereFitCentreWorld'])-opt['R']['posteriorSphereFitCentreWorld'])/.060;skinN=tree(P,T);skinA=tree(A,AT);arrays={'neutralFineWorld':P,'fineTriangles':T};report={}
 for side in ['L','R']:
  NV=(fullnative['GEO-head_animation_realistic.sclera.'+side+'-world']-C)*scale+C;NT=fullnative['GEO-head_animation_realistic.sclera.'+side+'-triangles'];AV=artist['eye'+side+'World'];ET=artist['eye'+side+'Triangles'];nc=(NV.min(0)+NV.max(0))/2;ac=(AV.min(0)+AV.max(0))/2;rn=(NV.max(0)-NV.min(0))/2;ra=(AV.max(0)-AV.min(0))/2;n=aperture(skinN,tree(NV,NT),NV);a=aperture(skinA,tree(AV,ET),AV);xmin,xmax=n[0,0],n[-1,0];axmin,axmax=a[0,0],a[-1,0];sx=(axmax-axmin)/(xmax-xmin);selected=np.flatnonzero((P[:,0]>xmin-.008)&(P[:,0]<xmax+.008)&(P[:,2]>n[:,1].min()-.008)&(P[:,2]<n[:,2].max()+.014)&(P[:,1]<nc[1]+.004));new={label:P.copy() for label in ['half','closed']};bindings=[]
  for vi in selected:
   p=P[vi];x= axmin+(p[0]-xmin)*sx;nl=np.interp(p[0],n[:,0],n[:,1]);nu=np.interp(p[0],n[:,0],n[:,2]);al=np.interp(x,a[:,0],a[:,1]);au=np.interp(x,a[:,0],a[:,2]);sz=max(au-al,1e-5)/max(nu-nl,1e-5);nm=(nu+nl)/2;am=(au+al)/2;sy=ra[1]/rn[1];query=np.array([x,ac[1]+(p[1]-nc[1])*sy,am+(p[2]-nm)*sz]);hit,no,fi,dist=skinA.find_nearest(Vector(query));tri=AT[fi];v=A[tri];xy=np.linalg.lstsq(np.column_stack((v[1]-v[0],v[2]-v[0])),np.array(hit)-v[0],rcond=None)[0];w=np.r_[1-xy.sum(),xy];w=np.maximum(w,0);w/=w.sum();outside=max(xmin-p[0],p[0]-xmax,0);above=max(p[2]-nu,0);below=max(nl-p[2],0);fade=max(0.,min(1.,1-outside/.008,1-above/.014,1-below/.008));fade=fade*fade*(3-2*fade)
   for label in new:
    delta=w@(artist[label+'World'][tri]-A[tri]);new[label][vi]=p+delta/np.array([sx,sy,sz])*fade
   bindings.append({'nativeVertex':int(vi),'artistTriangle':int(fi),'barycentric':w,'queryDistanceM':dist,'registeredAxisScale':[sx,sy,sz],'transitionWeight':fade})
  for label,W in new.items():arrays[side+'_'+label+'_fineDelta']=W-P;arrays[side+'_'+label+'_fineWorld']=W
  report[side]={'nativeVisibleApertureSamples':n,'artistVisibleApertureSamples':a,'selectedFullSheetAndShortWallNativeVertices':len(selected),'maxClosedMoveM':float(np.linalg.norm(new['closed']-P,axis=1).max()),'bindings':bindings,'noUVSeamAssumption':True,'actualFrontRayGridIsRegistrationNotGlobalContactProof':True,'finiteSelfContinuousContactUnaccepted':True}
 mesh=bpy.data.meshes.new('AFN109_ACTUAL_ARTIST_REGISTERED_NATIVE_LID_SHEET');mesh.from_pydata(P.tolist(),[],T.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);ob.shape_key_add(name='Basis')
 for side in ['L','R']:
  for label in ['half','closed']:ob.shape_key_add(name='AFN109_AUTHORING_'+side+'_'+label).data.foreach_set('co',arrays[side+'_'+label+'_fineWorld'].astype('f4').ravel())
 ob.hide_render=True;ob['scope']='Actual artist external-sheet neutral/half/closed deformation registered onto native complete ocular hood and short wall. Original native neutral geometry preserved. Artist pose data incorporated under CC-BY4.0; not a contact/closure acceptance.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'native-artist-sheet-authoring.blend'),compress=True);np.savez_compressed(E/'native-artist-sheet-poses.npz',**arrays);save('artist-sheet-authoring.json',{'construction':'Actual external artist sheet motion, visible aperture chart registration, whole native ocular hood/short wall pose reconstruction and fixed transition. No guessed native UV seam target, front-globe projection or Laplacian solver. Neutral native geometry exact; full character preview decides adoption.','artistSource':'Existing Blender Studio Ellie v1 / GEO-ellie_head / CC-BY4.0','artistActualPoseDataTransferred':True,'originalArtistSourceAndNoticesRetained':True,'poses':report,'seconds':time.time()-tick});print('R109_ACTUAL_ARTIST_LID_SHEET_AUTHORED',time.time()-tick,flush=True)
if __name__=='__main__':main()
