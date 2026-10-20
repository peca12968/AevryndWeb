"""Whole-groom reconstruction, not another inherited-curl registration.

One explicit layered side-part flow on the same actual roots. Native editable
guides drive indexed child offsets. Original fibre count, radius, Brown material,
root-frame metadata and complete woman's unrelated data are held fixed.
This is an art-directed static hypothesis, not natural dynamics/contact proof.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0089-posterior-growth'
SRC=S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend';OUT=S/'aevrynd-female-next-r0089-b-parted-layered-bob.blend'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('r89bob_source','build-female-next-r0081-editable-curly.py');q=m.q;v=module('r89bob_views','render-female-next-r0081-retained-study.py');v.E=E;a=module('r89bob_native','build-female-next-r0089-posterior-bundles.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def paths(roots,owner):
 # Artistic head contour scaffold, in metres. Never used as a collider.
 t=np.linspace(0,1,23)[None,:];X=roots[:,0,None];Y=roots[:,1,None];Z=roots[:,2,None];side=np.where(X<-.017,-1.,1.)
 theta=np.arctan2((Y+.04)/.092,X/.075);target=np.where(side>0,-.10,-np.pi+.10);turn=(target-theta+np.pi)%(2*np.pi)-np.pi
 front=1-smooth(-.090,-.050,Y);theta=theta+front*turn*smooth(0,.48,t)
 phase=owner[:,None]*2.3999632297;ends=1.333+.009*np.sin(phase)+.004*np.cos(roots[:,1,None]*56)
 z=Z+(ends-Z)*smooth(0,1,t)+.003*np.sin(np.pi*t)*(Z>1.51)
 rho=np.sqrt(np.maximum(.005,1-((np.maximum(z,1.450)-1.450)/.112)**2))
 lift=(.007+.0014*np.sin(2*np.pi*1.2*t+phase))*smooth(0,.22,t)
 radius=rho+lift/.083
 x=.075*radius*np.cos(theta);y=-.04+.092*radius*np.sin(theta)
 raw=np.stack((x,y,z),axis=2);delta=roots-raw[:,0];raw+=delta[:,None,:]*(1-smooth(0,.26,t))[:,:,None]
 # A quiet inward tip bend and shared low-frequency strand grouping.
 bend=smooth(.68,1,t);raw[:,:,0]-=.006*side*bend;raw[:,:,1]-=.003*np.sin(theta)*bend
 raw[:,0]=roots
 return raw
def curves(name,P,radius,A,material):
 d=bpy.data.hair_curves.new(name+'_DATA');d.add_curves([23]*len(P));d.position_data.foreach_set('vector',P.astype('f4').ravel());ra=d.attributes.get('radius') or d.attributes.new('radius','FLOAT','POINT');ra.data.foreach_set('value',np.asarray(radius,'f4').ravel());d.materials.append(material)
 o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.matrix_world=A.copy();return o
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();old=bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'];A=old.matrix_world.copy();AA=np.array(A);inv=np.linalg.inv(AA[:3,:3]);baseline=q.hair(old).copy();ed=old.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;counts=np.array([c.points_length for c in ed.curves]);assert np.all(counts==23);starts=np.r_[0,np.cumsum(counts)[:-1]];radii=q.arr(ed.attributes['radius'].data,'value',len(baseline)).copy();materials={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes};lights=m.m.q.lights()
 for n in ('AFN81_ACTUAL_RENDER_ROOT_TABLE','AFN81_LIVE_RENDER_SCALP_FRAME'):old.modifiers[n].show_viewport=old.modifiers[n].show_render=False
 bpy.context.view_layer.update();source=q.hair(old).copy();roots=source[starts];nativeCounts=np.array([c.points_length for c in old.data.curves]);nativeStarts=np.r_[0,np.cumsum(nativeCounts)[:-1]];native=q.arr(old.data.position_data,'vector',len(old.data.position_data),3).astype('f8');guideRoots=(native[nativeStarts]@AA[:3,:3].T+AA[:3,3]);owners=np.empty(len(roots),'i4')
 # Keep part-side membership during nearest-guide assignment.
 trees={}
 for side in (-1,1):
  ids=np.flatnonzero(np.where(guideRoots[:,0]<-.017,-1,1)==side);tree=KDTree(len(ids))
  for i in ids:tree.insert(Vector(guideRoots[i]),int(i))
  tree.balance();trees[side]=tree
 for i,p in enumerate(roots):owners[i]=trees[-1 if p[0]<-.017 else 1].find(Vector(p))[1]
 G=paths(guideRoots,np.arange(len(guideRoots)));P=paths(roots,owners);PL=(P-AA[:3,3])@inv.T;GL=(G-AA[:3,3])@inv.T
 guide=curves('AFN89_PARTED_BOB_EDITABLE_GUIDES',GL,np.full((len(G),23),.001,'f4'),A,bpy.data.materials['Brown hair']);guide.hide_render=True;guide.hide_set(True);guide.data.surface=bpy.data.objects['AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE'];guide['scope']='303 native editable23-point layered-bob guides. World contour scaffold is art direction, not anatomical distance or collider. Child table holds initial residuals; editing guide points changes children before existing actual-root following. No natural dynamics.'
 child=curves('AFN89_PARTED_BOB_RENDER_CURVES',PL,radii.reshape(-1,23),A,bpy.data.materials['Brown hair']);meta=a.pointmesh('AFN89_BOB_CHILD_GUIDE_POINT_TABLE',np.zeros((len(source),3)),A);meta.hide_set(True)
 ids=(owners[:,None]*23+np.arange(23)[None,:]).ravel().astype('i4');offset=(PL-GL[owners]).reshape(-1,3).astype('f4');w=np.ones(len(source),'f4');w[starts]=0
 a.attribute(meta.data,'AFN89_GuidePointID','INT',ids);a.attribute(meta.data,'AFN89_ReferenceBundleOffset','FLOAT_VECTOR',offset);a.attribute(meta.data,'AFN89_RegionalWeight','FLOAT',w)
 # Reuse the verified indexed live-guide construction; all shafts, no regional mix.
 dummy=child.modifiers.new('TEMP_PUBLISHER_SLOT','NODES');dummy.node_group=bpy.data.node_groups.new('AFN81_PUBLISHER_CURLY_PROGRAM_BOB_DUMMY','GeometryNodeTree');dummy.show_viewport=dummy.show_render=False
 md=a.graph(child,guide,meta);md.name='AFN89_WHOLE_GROOM_LIVE_GUIDES';child.modifiers.remove(dummy)
 for n in ('AFN81_ACTUAL_RENDER_ROOT_TABLE','AFN81_LIVE_RENDER_SCALP_FRAME'):
  old.modifiers[n].show_viewport=old.modifiers[n].show_render=True;new=child.modifiers.new(n,'NODES');new.node_group=old.modifiers[n].node_group
 old.hide_render=True;old.hide_set(True);bpy.context.view_layer.update();Q=q.hair(child);d=child.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;assert Q.shape==baseline.shape and np.isfinite(Q).all();assert np.array_equal(q.arr(d.attributes['radius'].data,'value',len(Q)),radii);err=float(np.linalg.norm(Q[starts]-baseline[starts],axis=1).max());assert err<2e-6;assert np.array_equal(np.array([c.points_length for c in d.curves]),counts);assert materials=={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes} and lights==m.m.q.lights()
 child['scope']='Whole-groom art reconstruction. Same21908 actual indexed roots and original physical radii/skin-root tables;303 new editable guides. Old curly source retained hidden. Not head-skin motion, contact or natural dynamics qualification.';s['AFN89_B_scope']=child['scope'];m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 np.savez_compressed(E/'b-parted-bob-lineage.npz',sourceRawWorld=source,sourceEvaluatedWorld=baseline,sourceCounts=counts,sourceRadii=radii,guideRootWorld=guideRoots,guideWorld=G,childWorld=P,actualChildWorld=Q,childOwners=owners,childGuidePointIDs=ids,childOffsetsLocal=offset,matrix=AA)
 save('b-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'construction':'Complete side-part layered-bob flow replaces inherited curl generator, all21908 actual follicles retained. Native303 editable guides + per-child indexed residuals + existing actual-root frame. Artistic contour scaffold, not measured anatomy or collision solution.','guideObject':guide.name,'renderObject':child.name,'nativeGuides':len(G),'guidePointsEach':23,'actualCurves':len(counts),'actualPoints':len(Q),'worldRootMaximumDifferenceM':err,'originalRadiusCountAndMaterialsPreserved':True,'oldCurlyRetainedHidden':True,'newAppearanceContactDynamicsRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ('back','face','body-face'):rows.append(v.image('b-parted-bob',view));save('b-pilot-controls.json',rows)
 print('R89_WHOLE_PARTED_BOB_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
