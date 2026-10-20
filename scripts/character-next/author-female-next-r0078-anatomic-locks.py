"""Authored lower lock corridors on the same complete woman.
Crown/root paths stay; new side/back rest geometry follows explicit anatomical
cross-sections, layered terminal heights and separated angular bundles.
This is static groom authoring, not a deformation/physics length constraint.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0078-anatomic-locks';SRC=S/'aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend';OUT=S/'aevrynd-female-next-r0078-a-anatomic-locks-study.blend';SHA='bd8e5bb124756aa486a6a00b26a2a5cf2ca4438cf122ef3a756b172d1c3ba3f5'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('locks78render','build-female-next-r0074-oral-controls.py');q=module('locks78data','qualify-female-next-r0075-dental-motion.py');m.E=E;m.m.shade.g.E=E
REBUILD='--rebuild-nape' in sys.argv
ROUTED='--routed-corridors' in sys.argv or REBUILD
TAG='c' if REBUILD else ('b' if ROUTED else 'a')
if ROUTED:OUT=S/('aevrynd-female-next-r0078-c-scalp-bound-locks-study.blend' if REBUILD else 'aevrynd-female-next-r0078-b-routed-anatomic-locks-study.blend')
CY=.015;N=24

def save(n,v):(E/n).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'];d,V=q.geom(body);d.calc_loop_triangles();T=np.array([t.vertices[:] for t in d.loop_triangles]);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True)
 angles=np.linspace(-np.pi,np.pi,96,endpoint=False);heights=np.linspace(1.325,1.505,64);envelope=np.zeros((len(heights),len(angles)))
 for zi,z in enumerate(heights):
  for ai,theta in enumerate(angles):
   direction=Vector((float(np.cos(theta)),float(np.sin(theta)),0.));origin=Vector((0.,CY,float(z)));last=None
   for _ in range(24):
    co,normal,face,distance=tree.ray_cast(origin,direction,.5)
    if co is None:break
    last=np.array(co);origin=co+direction*1e-6
   assert last is not None,(zi,ai);envelope[zi,ai]=np.linalg.norm(last[:2]-np.array((0.,CY)))
 def bound(theta,z):
  x=((theta+np.pi)%(2*np.pi))/(2*np.pi)*len(angles);i=int(np.floor(x))%len(angles);j=(i+1)%len(angles);a=x-np.floor(x);return (1-a)*np.interp(z,heights,envelope[:,i])+a*np.interp(z,heights,envelope[:,j])
 o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];P=q.arr(o.data.position_data,'vector',len(o.data.position_data),3).copy();A=np.array(o.matrix_world);inv=np.linalg.inv(A);world=P.astype('f8')@A[:3,:3].T+A[:3,3];counts=np.array([c.points_length for c in o.data.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];rr=q.arr(o.data.attributes['radius'].data,'value',len(P)).copy();new=world.copy();group=np.full(len(counts),-1,'i4');entry=np.full(len(counts),-1,'i4');pins=np.ones(len(P),bool);guide_rows=[];changed=0;rebuiltRoots=[]
 def corridor(anchor,theta,layer,endz,radial_offset,t,angularKnots=None):
  center=np.round(theta/(2*np.pi/N))*(2*np.pi/N);phase=(theta-center)*(1-.6*smooth(t));az=center+phase+.045*np.cos(center)*np.sin(np.pi*t)+.020*np.sin(center*5)*t*t
  if angularKnots is not None:
   endcenter=np.round(angularKnots[-1]/(2*np.pi/N))*(2*np.pi/N);az=np.interp(t,np.linspace(0,1,5),angularKnots)+(endcenter-angularKnots[-1])*.40*smooth(t)
  r0=np.linalg.norm(anchor[:2]-np.array((0.,CY)));radial=np.interp(t,[0,.25,.60,.84,1.],[r0,max(r0,.104),.108,.100,.087+.007*layer]);radial+=.002*np.sin(center*3)*np.sin(np.pi*t)+radial_offset*np.sin(np.pi*t)
  z=(1-t)*anchor[2]+t*endz
  # Geometric design envelope only. Independent saved cubic/tube contact
  # verification is still required; this grid is never a contact certificate.
  safe=np.array([bound(float(a),float(h))+.008 for a,h in zip(az,z)]);radial=np.maximum(radial,safe)
  path=np.column_stack((radial*np.cos(az),CY+radial*np.sin(az),z));path[0]=anchor;return path
 for ci,(st,ct) in enumerate(zip(starts,counts)):
  p=world[st:st+ct]
  if REBUILD and p[0,2]<1.47:
   theta=float(np.arctan2(p[0,1]-CY,p[0,0]));theta=theta if p[0,0]>=0 else (theta%(2*np.pi));theta=float(np.clip(theta,-.65,np.pi+.65));theta+=.22*np.cos(theta);rootz=max(1.455,float(p[0,2]));direction=Vector((float(np.cos(theta)),float(np.sin(theta)),0.));co,normal,face,distance=tree.ray_cast(Vector((0.,CY,rootz)),direction,.3);assert co is not None
   normal=np.array(normal);newroot=np.array(co)+normal*(float(rr[st])*np.linalg.norm(A[:3,:3],ord=2)+8e-6);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];u=arc/arc[-1];endz=1.372+.004*np.sin(theta*3);route=np.linspace(theta,theta+.14*np.cos(theta),5);path=corridor(newroot,theta,0.,endz,0.,u,route);path[0]=newroot;new[st:st+ct]=path;pins[st:st+ct]=False;entry[ci]=0;group[ci]=2000+int(np.round(theta/(2*np.pi/N)))%N;changed+=1;rebuiltRoots.append({'curve':ci,'sourceRoot':p[0].tolist(),'newRoot':newroot.tolist(),'actualSkinTriangle':int(face),'surfacePoint':list(co),'normal':normal.tolist(),'radiusStandOffM':float(rr[st])*np.linalg.norm(A[:3,:3],ord=2)+8e-6,'method':'First displayed-skin ray hit at an authored side/back height; no independent scalp/pinna or follicle-lumen acceptance. Rejected root relocation.'})
   if not any(row['group']==int(group[ci]) for row in guide_rows):guide_rows.append({'group':int(group[ci]),'sourceCurve':ci,'region':'rebuilt-nape','layer':0.,'sourceAnchor':newroot.tolist(),'terminalHeightM':endz,'routeAngularKnots':route.tolist(),'points':corridor(newroot,theta,0.,endz,0.,np.linspace(0,1,33),route).tolist()})
   continue
  suffix=np.maximum.accumulate(p[::-1,2])[::-1];eligible=np.flatnonzero(suffix<1.49)
  if not len(eligible):continue
  k=max(1,int(eligible[0]));k=min(k+1,int(ct)-1)
  if ct-k<4 or p[k,2]<1.405:continue
  anchor=p[k];theta=float(np.arctan2(anchor[1]-CY,anchor[0]));layer=float(np.clip((p[0,2]-1.49)/.08,0,1));endz=1.375-.027*layer+.003*np.sin(theta*3)+.005*np.tanh((p[-1,2]-1.36)/.015);endz=min(endz,float(anchor[2]-.025));t=np.linspace(0,1,int(ct)-k);radial_offset=.002*np.sin(ci*.61803398875);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p[k:],axis=0),axis=1))];arc/=arc[-1];route=np.unwrap(np.arctan2(p[k:,1]-CY,p[k:,0]));angularKnots=np.interp(np.linspace(0,1,5),arc,route) if ROUTED else None;path=corridor(anchor,theta,layer,endz,radial_offset,t,angularKnots)
  # A Hermite entrance matches the old incoming tangent rather than forcing
  # edge lengths or pulling dense strands onto a shared point target.
  incoming=p[k]-p[k-1];incoming=incoming/max(np.linalg.norm(incoming),1e-20);span=anchor[2]-endz;desired=(path[1]-path[0])/(t[1]-t[0]);derivative=incoming*(span/max(-incoming[2],.35));correction=derivative-desired;path+=((t*(1-t)**3)[:,None])*correction[None,:];path[0]=anchor
  new[st+k:st+ct]=path;entry[ci]=k;group[ci]=(int(np.round(theta/(2*np.pi/N)))%N)*N+(int(np.round(route[-1]/(2*np.pi/N)))%N)+N*N*int(layer>=.5) if ROUTED else int(np.round(theta/(2*np.pi/N)))%N+N*int(layer>=.5);pins[st+k+1:st+ct]=False;changed+=1
  if not any(row['group']==int(group[ci]) for row in guide_rows):guide_rows.append({'group':int(group[ci]),'sourceCurve':ci,'region':'side' if abs(np.cos(theta))>.60 else 'back/front-margin','layer':layer,'sourceAnchor':anchor.tolist(),'terminalHeightM':float(endz),'routeAngularKnots':angularKnots.tolist() if angularKnots is not None else None,'points':corridor(anchor,theta,layer,endz,0.,np.linspace(0,1,33),angularKnots).tolist()})
 delta=np.linalg.norm(new-world,axis=1);bad=int(np.argmax(delta));owner=int(np.searchsorted(starts,bad,side='right')-1);extentLow=world.min(0)-.02;extentHigh=world.max(0)+.02;insideExtent=bool(np.all(new>=extentLow) and np.all(new<=extentHigh));guard=bool(np.isfinite(new).all() and (insideExtent if REBUILD else delta.max()<.1));save((TAG+'-geometry-guard.json'),{'finite':bool(np.isfinite(new).all()),'maximumDisplacementM':float(delta.max()),'curve':owner,'sourcePointM':world[bad].tolist(),'proposedPointM':new[bad].tolist(),'envelopeRadiusRangeM':[float(envelope.min()),float(envelope.max())],'limitM':None if REBUILD else .1,'oldDisplacementGuardPassed':bool(delta.max()<.1),'replacementGuard':('Actual complete source hair extent plus20mm; root-reference origins are reauthored, so old point-displacement threshold is not an anatomy/contact criterion. Require new binding/readback, anatomy review and affected contact evidence; no inherited contact acceptance.' if REBUILD else None),'extentLowM':extentLow.tolist(),'extentHighM':extentHigh.tolist(),'insideExtent':insideExtent,'passed':guard});
 if not guard:np.savez_compressed(E/(TAG+'-failed-path.npz'),source=world[starts[owner]:starts[owner]+counts[owner]],proposed=new[starts[owner]:starts[owner]+counts[owner]],envelopeAngles=angles,envelopeHeights=heights,envelopeRadii=envelope)
 assert guard;
 local=new@inv[:3,:3].T+inv[:3,3];local[pins]=P[pins];o.data.position_data.foreach_set('vector',local.astype('f4').ravel());o.data.update_tag();assert changed>1000
 col=bpy.data.collections.new('AFN78_ANATOMIC_LOCK_AUTHORING');s.collection.children.link(col);cu=bpy.data.curves.new('AFN78_EXPLICIT_SIDE_BACK_CORRIDORS','CURVE');cu.dimensions='3D';cu.resolution_u=1
 for row in guide_rows:
  sp=cu.splines.new('POLY');sp.points.add(len(row['points'])-1);sp.points.foreach_set('co',np.column_stack((row['points'],np.ones(len(row['points'])))).astype('f4').ravel())
 helper=bpy.data.objects.new(cu.name,cu);col.objects.link(helper);helper.hide_render=True;helper.hide_set(True);helper['scope']='Neutral-only explicit anatomical guide corridors; no live groom edit or physical simulation acceptance.'
 for name,data in [('AFN78_LockGroup',group),('AFN78_LowerEntryIndex',entry)]:at=o.data.attributes.new(name,'INT','CURVE');at.data.foreach_set('value',data)
 o['AFN78_scope']=('Rejected static groom with1725 relocated low roots and rebuilt root frames; remaining source prefix pinned. No anatomy, contact, natural motion or runtime acceptance.' if REBUILD else 'Authored lower rest paths; source root/crown prefix, counts/radii/material/bindings retained; no contact or dynamics acceptance.')
 np.savez_compressed(E/(TAG+'-lower-lock-lineage.npz'),sourceLocal=P,outputLocal=local.astype('f4'),sourceWorld=world,starts=starts,counts=counts,radii=rr,matrix=A,pinned=pins,groups=group,entry=entry,envelopeAngles=angles,envelopeHeights=heights,envelopeRadii=envelope)
 save((TAG+'-authored-guides.json'),{'representation':'Explicit side/back anatomical corridors and variable layer lengths, no common tangent/curl field or forced source-edge length solve.','centerY':CY,'actualDisplayedSkinUsedForEnvelope':body.name,'radialEnvelopeGridOnlyAuthoringAidNotCertificate':True,'guideRows':guide_rows})
 if REBUILD:
  for md in list(o.modifiers):
   if md.name=='AFN69_LIVE_RENDER_SCALP_FRAME':o.modifiers.remove(md)
  for at in list(o.data.attributes):
   if at.name.startswith('AFN69_'):o.data.attributes.remove(at)
  rig=m.m;rig.E=E;actualBody=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];row=rig.k.mesh(actualBody);bodyTree=BVHTree.FromPolygons(row['V'].tolist(),row['T'].tolist(),all_triangles=True);binding=rig.follower(o,actualBody,bpy.data.objects['AFN69_REST_BODY_POINT_REFERENCE'],row,bodyTree);save('c-new-root-binding.json',{'binding':binding,'rebuiltRoots':rebuiltRoots,'noNaturalMotionOrContactAcceptance':True})
 bpy.context.view_layer.update();m.m.shade.settings();m.m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;s['AFN78_scope']='Complete source with anatomically authored lower hair locks. Static appearance study, no natural motion or engine acceptance.';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 save((TAG+'-build-summary.json'),{'source':str(SRC),'sourceSha256':SHA,'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'changedCurves':changed,'curves':len(counts),'points':len(P),'guideGroups':len(guide_rows),'exactPinnedPoints':int(pins.sum()),'rebuiltNapeRoots':len(rebuiltRoots),'existingRootBindingsRetained':not REBUILD,'maximumRestPointDisplacementM':float(delta.max()),'nativeRadiusMaterialSkinOralRigLightUnedited':True,'edgeLengthsIntentionallyReauthoredNotMotionStretch':True,'naturalMotionContactRuntimeAccepted':False,'secondsBeforePilot':time.time()-tick})
 controls=[]
 for view in ('face','body-face'):controls.append(m.render(TAG+'-pilot',view));save((TAG+'-pilot-controls.json'),controls)
 print('R78_ANATOMIC_COMPLETE_PREVIEW_DONE',changed,len(guide_rows),time.time()-tick,flush=True)
if __name__=='__main__':main()
