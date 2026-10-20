"""Single full-character groom: authored guide combing, exact root pins and native edge lengths.
Static art production only. Not a natural-motion solver or contact certificate.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time,importlib.util,sys
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0077-guided-tip-groom'
SRC=S/'aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend';OUT=S/'aevrynd-female-next-r0077-a-guided-tip-groom-study.blend';SHA='bd8e5bb124756aa486a6a00b26a2a5cf2ca4438cf122ef3a756b172d1c3ba3f5'
ROUNDED='--rounded-locks' in sys.argv
TANGENT='--tangent-only' in sys.argv or ROUNDED
TAG='c' if ROUNDED else ('b' if TANGENT else 'a')
if TANGENT:OUT=S/('aevrynd-female-next-r0077-c-rounded-lock-groom-study.blend' if ROUNDED else 'aevrynd-female-next-r0077-b-local-tip-comb-study.blend')
sp=importlib.util.spec_from_file_location('groom77render',Path(__file__).with_name('build-female-next-r0074-oral-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.E=E;m.m.shade.g.E=E
HAIR=('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES')
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def arr(d):
 a=np.empty(len(d)*3,'f4');d.foreach_get('vector',a);return a.reshape(-1,3).astype('f8')
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def sampled(p,n=64):
 t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];assert t[-1]>1e-8;u=t/t[-1];v=np.linspace(0,1,n);return np.stack([np.interp(v,u,p[:,j]) for j in range(3)],axis=1),u

def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects[HAIR[0]];A=np.array(o.matrix_world);inv=np.linalg.inv(A);P=arr(o.data.position_data);world=P@A[:3,:3].T+A[:3,3];counts=np.array([c.points_length for c in o.data.curves],dtype='i4');starts=np.r_[0,np.cumsum(counts)[:-1]];paths=[world[st:st+ct] for st,ct in zip(starts,counts)];samples=[];us=[]
 for p in paths:q,u=sampled(p);samples.append(q);us.append(u)
 samples=np.array(samples);feature=np.concatenate((samples[:,0]*1.5,samples[:,30],samples[:,-1]*.35),axis=1);first=int(np.argmax(samples[:,0,2]));chosen=[first];nearest=np.sum((feature-feature[first])**2,axis=1)
 for _ in range(59):
  idx=int(np.argmax(nearest));chosen.append(idx);nearest=np.minimum(nearest,np.sum((feature-feature[idx])**2,axis=1))
 distances=np.sum((feature[:,None]-feature[np.array(chosen)][None])**2,axis=2);groups=distances.argmin(1);guideold=samples[chosen];guidenew=guideold.copy();grid=np.linspace(0,1,64)
 # Hand-directed lower side/back comb: retain crown and parting, rotate flared
 # tips downward with a slight posterior sweep. Per-guide native length stays.
 for gi,g in enumerate(guideold):
  q=g.copy();side=np.sign(g[40,0]);flow=np.array((side*.10,.20,-1.));flow/=np.linalg.norm(flow)
  for k in range(1,len(g)):
   edge=g[k]-g[k-1];length=np.linalg.norm(edge);w=float(smooth((grid[k]-.32)/.48)*smooth((1.52-g[k,2])/.11))*.86
   tangent=edge/length;new=tangent*(1-w)+flow*w;new/=np.linalg.norm(new);q[k]=q[k-1]+new*length
  guidenew[gi]=q
 newworld=world.copy();pins=[];rows=[]
 for ci,(st,ct,p,u,group) in enumerate(zip(starts,counts,paths,us,groups)):
  oldg=np.stack([np.interp(u,grid,guideold[group,:,j]) for j in range(3)],axis=1);newg=np.stack([np.interp(u,grid,guidenew[group,:,j]) for j in range(3)],axis=1)
  clump=.48*smooth((u-.30)/.45);desired=newg+(p-oldg)*(1-clump[:,None]);q=p.copy();lengths=np.linalg.norm(np.diff(p,axis=0),axis=1)
  pinned=u<=.25;pins.extend((st+np.flatnonzero(pinned)).tolist())
  for k in range(1,ct):
   if pinned[k]:continue
   direction=desired[k]-q[k-1];direction/=np.linalg.norm(direction);q[k]=q[k-1]+direction*lengths[k-1]
  if TANGENT:
   # Anatomical suffix selection prevents combing upper/returning curls.
   # Rotate native edge tangents; never attract strand positions to a center.
   q=p.copy();suffix=np.maximum.accumulate(p[::-1,2])[::-1];eligible=(u>.45)&(suffix<1.49);first=np.flatnonzero(eligible)
   if len(first):
    start=int(first[0]);flow=np.array((np.sign(guideold[group,40,0])*.10,.20,-1.));flow/=np.linalg.norm(flow)
    for k in range(start,ct):
     if k==0:continue
     w=.90*float(smooth((u[k]-.40)/.40)*smooth((1.49-p[k,2])/.10))
     if ROUNDED:
      azimuth=np.arctan2(guideold[group,40,1]-.02,guideold[group,40,0]);radial=np.array((np.cos(azimuth),np.sin(azimuth),0.));curl=float(smooth((u[k]-.69)/.31));angle=.08-(.84+.16*np.sin(azimuth*3))*curl;flow=radial*np.sin(angle)+np.array((0.,.10,-np.cos(angle)));flow/=np.linalg.norm(flow)
     edge=(p[k]-p[k-1])/lengths[k-1];direction=(1-w)*edge+w*flow;direction/=np.linalg.norm(direction);q[k]=q[k-1]+direction*lengths[k-1]
   pins.extend((st+np.flatnonzero(~eligible)).tolist())
  newworld[st:st+ct]=q
 if TANGENT:guidenew=np.array([sampled(newworld[starts[ci]:starts[ci]+counts[ci]])[0] for ci in chosen])
 delta=np.linalg.norm(newworld-world,axis=1);assert np.isfinite(newworld).all() and delta.max()<.10
 local=newworld@inv[:3,:3].T+inv[:3,3];local[np.array(pins)]=P[np.array(pins)];o.data.position_data.foreach_set('vector',local.astype('f4').ravel());o.data.update_tag()
 oldradius=np.empty(len(P),'f4');o.data.attributes['radius'].data.foreach_get('value',oldradius);newradius=oldradius.copy()
 if ROUNDED:
  for st,ct,u in zip(starts,counts,us):newradius[st:st+ct]=oldradius[st:st+ct]*(1-.95*smooth((u-.70)/.30))
  o.data.attributes['radius'].data.foreach_set('value',newradius);o.data.update_tag()
 # Editable structural guides are actual curves. They are authoring helpers,
 # hidden from render, with explicit neutral-only status, not a second hairstyle.
 col=bpy.data.collections.new('AFN77_EDITABLE_STATIC_GROOM_GUIDES');s.collection.children.link(col)
 d=bpy.data.curves.new('AFN77_SIXTY_COMBED_GUIDES','CURVE');d.dimensions='3D';d.resolution_u=1
 for g in guidenew:
  spline=d.splines.new('POLY');spline.points.add(len(g)-1);spline.points.foreach_set('co',np.column_stack((g,np.ones(len(g)))).astype('f4').ravel())
 guide=bpy.data.objects.new(d.name,d);col.objects.link(guide);guide.hide_render=True;guide.hide_set(True);guide['scope']='Neutral-only authored static guides; no rig following, physical motion or runtime acceptance.'
 for name,value in [('AFN77_GuideIndex',groups.astype('i4')),('AFN77_SourceCurveIndex',np.arange(len(counts),dtype='i4'))]:a=o.data.attributes.new(name,'INT','CURVE');a.data.foreach_set('value',value)
 o['AFN77_scope']='Static guide-directed mid/tip grooming. Roots and first25% native arc pinned; native control-polygon edge lengths retained. Catmull-Rom true arc length, finite strand contact and natural hair physics not thereby accepted.'
 np.savez_compressed(E/(TAG+'-groom-lineage.npz'),sourceLocal=P.astype('f4'),sourceWorld=world,outputLocal=local.astype('f4'),counts=counts,starts=starts,pinnedPointIDs=np.array(pins,'i4'),guideSourceCurveIDs=np.array(chosen,'i4'),groups=groups.astype('i4'),guideOld=guideold,guideNew=guidenew,matrix=A,sourceRadii=oldradius,outputRadii=newradius)
 bpy.context.view_layer.update();m.m.shade.settings();m.m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;s['AFN77_scope']='Complete woman with static guide-directed tip grooming only; original material, radii, skin, mouth and rig preserved. No new dynamics/contact/runtime acceptance.';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 save(TAG+'-build-summary.json',{'source':str(SRC),'sourceSha256':SHA,'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'method':('Anatomically pinned upper paths,60 spatial bundle directions with authored inward-rounded terminal arcs and explicit last30% radius taper. Native polygon edge lengths retained; static grooming only.' if ROUNDED else 'Anatomically restricted ear-below native tangent comb, sixty group flow directions and representative editable guides. No positional clump attraction; all upper/returning paths pinned. Native edge lengths retained.' if TANGENT else 'Sixty spatial/path-coherent existing strand guides, lower tangent comb, finite-spread positional convergence and edge-length reconstruction; rejected for new temple loops.'),'curves':len(counts),'points':len(P),'pinnedPoints':len(set(pins)),'guideCount':len(chosen),'maximumPointDisplacementM':float(delta.max()),'medianPointDisplacementM':float(np.median(delta)),'sourceMaterialSkinRigLightUnedited':True,'radiusChangedOnlyByTerminalTaper':ROUNDED,'radiusRootShaftUnchangedThroughArcFraction':.70 if ROUNDED else 1.,'taperDoesNotWaiveContact':True,'noNaturalHairOrWholeContactAcceptance':True,'secondsBeforePilot':time.time()-tick})
 controls=[]
 for view in ('face','body-face'):controls.append(m.render(TAG+'-pilot',view));save(TAG+'-pilot-controls.json',controls)
 print('R77_COMPLETE_GROOM_PILOT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
