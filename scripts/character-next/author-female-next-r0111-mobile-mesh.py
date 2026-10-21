"""Actual replacement ocular meshes, own artist topology and finite lid wall.

An entire local Rain surface/paired optics is staged as geometry; no Rain pose
delta is transferred to the old Dan Ulrich eye mesh. Collar fit is authored on
the new mesh and fixed at its outside boundary. Full-character preview decides.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0111-native-mobile-lid-mesh';SRC=R/'Reference/character/blender-studio-rain-v3-cc-by4/Rain v3.3/rain_v3.2.blend';PRE=E.parent/'r0107-native-coarse-lid-cage'
sp=importlib.util.spec_from_file_location('r111mesh',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def main():
 tick=time.time()
 if not (E/'mobile-mesh-authoring-start.json').exists():save('mobile-mesh-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Author actual replacement Rain ocular surface topology, paired eyes and finite short wall; fixed collar on new geometry, no old-mesh pose transfer.'})
 d=np.load(E/'actual-rain-ocular-geometry.npz');native=np.load(PRE/'native-coarse-lid-poses-pinned.npz');P=native['neutralFineWorld'];T=native['fineTriangles'];oldtree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True);opt=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];original=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');C=np.mean([r['posteriorSphereFitCentreWorld'] for r in opt.values()],0);scale=np.linalg.norm(np.array(opt['L']['posteriorSphereFitCentreWorld'])-opt['R']['posteriorSphereFitCentreWorld'])/.060;parts=[];headV=[];headF=[];poses={k:[] for k in ['L_half','L_closed','R_half','R_closed']};offset=0;report={};arrays={};cut=np.zeros(len(T),bool)
 for side,sign in [('L',1),('R',-1)]:
  eye=d['eyes_neutralWorld'];ev=eye[eye[:,0]*sign>0];sc=(ev.min(0)+ev.max(0))/2;nv=(original['GEO-head_animation_realistic.sclera.'+side+'-world']-C)*scale+C;nc=(nv.min(0)+nv.max(0))/2;s=float(np.ptp(nv[:,0])/np.ptp(ev[:,0]));A=np.eye(4);A[:3,:3]*=s;A[:3,3]=nc-sc*s;h=(d['head_neutralWorld']-sc)*s+nc;HT=d['head_neutralTriangles'];ct=h[HT].mean(1);selected=np.flatnonzero((abs(ct[:,0]-nc[0])<.028)&(abs(ct[:,2]-nc[2])<.024)&(ct[:,1]<nc[1]+.012));used=np.unique(HT[selected]);inverse=np.full(len(h),-1,int);inverse[used]=np.arange(len(used));N=h[used].copy();border=np.maximum(abs(N[:,0]-nc[0])/.028,abs(N[:,2]-nc[2])/.024);fit=np.clip((border-.70)/.30,0,1);fit=fit*fit*(3-2*fit);collar=np.zeros_like(N)
  for j in np.flatnonzero(fit>0):
   hit,no,fi,dist=oldtree.find_nearest(Vector(N[j]));collar[j]=(np.array(hit)-N[j])*fit[j]
  neutral=N+collar;headV.append(neutral);headF.append(inverse[HT[selected]]+offset)
  for key in poses:
   kside,label=key.split('_');V=neutral.copy()
   if kside==side:V+=(d['head_'+label+'World'][used]-d['head_neutralWorld'][used])*s*(1-fit[:,None])
   poses[key].append(V)
  arrays[side+'_sourceArtistVertexIDs']=used;arrays[side+'_sourceArtistTriangleIDs']=selected;arrays[side+'_collarFitWeight']=fit;arrays[side+'_sourceToNativeMatrix']=A;parts.append({'side':side,'start':offset,'count':len(used)});offset+=len(used);tc=P[T].mean(1);local=(abs(tc[:,0]-nc[0])<.020)&(abs(tc[:,2]-nc[2])<.015)&(tc[:,1]<nc[1]+.025);cut|=local;report[side]={'newArtistSurfaceVertices':len(used),'newArtistSurfaceTriangles':len(selected),'uniformPairedOcularScale':s,'sourceEyeCentre':sc,'targetEyeCentre':nc,'collarFittedVertices':int(np.count_nonzero(fit>0)),'maximumCollarFitM':float(np.linalg.norm(collar,axis=1).max()),'nativeTrianglesToReplace':int(np.count_nonzero(local)),'oldCompleteSourceRetainedNotDeleted':True}
  for name in ['eyes','cornea']:
   EV=d[name+'_neutralWorld'];ET=d[name+'_neutralTriangles'];chosen=np.flatnonzero(np.all(EV[ET,0]*sign>0,axis=1));ids=np.unique(ET[chosen]);inv=np.full(len(EV),-1,int);inv[ids]=np.arange(len(ids));arrays[name+'_'+side+'_sourceVertexIDs']=ids;arrays[name+'_'+side+'_sourceTriangleIDs']=chosen;arrays[name+'_'+side+'_triangles']=inv[ET[chosen]]
   for state in ['neutral','half','closed']:arrays[name+'_'+side+'_'+state+'World']=(d[name+'_'+state+'World'][ids]-sc)*s+nc
 V=np.concatenate(headV);F=np.concatenate(headF);mesh=bpy.data.meshes.new('AFN111_MOBILE_FINITE_OCULAR_SKIN');mesh.from_pydata(V.tolist(),[],F.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);ob.shape_key_add(name='Basis')
 for key,rows in poses.items():ob.shape_key_add(name='AFN111_'+key).data.foreach_set('co',np.concatenate(rows).astype('f4').ravel())
 for p in mesh.polygons:p.use_smooth=True
 md=ob.modifiers.new('AFN111_FINITE_LID_WALL_0p8MM','SOLIDIFY');md.thickness=.0008;md.offset=-1.;md.use_even_offset=True;ob['scope']='Actual replacement source artist surface/own keys with0.8mm finite wall, fixed new-mesh collar. Source topology used directly. Contact/attachment/anatomy and natural full operation unaccepted. Replaces native ocular port, not an overlaid hidden-failure skin mask.';arrays['patchNeutralWorld']=V;arrays['patchTriangles']=F;arrays['removedNativeSourceTriangles']=np.flatnonzero(cut)
 for key,rows in poses.items():arrays['patch_'+key+'World']=np.concatenate(rows)
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'mobile-ocular-authoring.blend'),compress=True);np.savez_compressed(E/'mobile-ocular-authoring.npz',**arrays);save('mobile-ocular-authoring.json',{'construction':'Direct new artist ocular surface and paired-eye mesh replacement, fixed new-mesh collar and0.8mm Solidify short wall. Own artist topology/pose vertices used; no pose field transferred to old skin. Native outer body will receive actual cut ports; original full source stays immutable.','artist':'Rain Rig (CC) Blender Foundation | studio.blender.org / CC-BY4.0','parts':parts,'poses':report,'sourceOriginalZip':'source-inputs/r0090-rain-rig/Rain-v3.3.zip','noFiniteContactOrWatertightAttachmentClaim':True,'seconds':time.time()-tick});print('R111_NEW_FINITE_MOBILE_OCULAR_MESH_AUTHORED',time.time()-tick,flush=True)
if __name__=='__main__':main()
