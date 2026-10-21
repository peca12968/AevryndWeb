"""Sculpt the actual anterior native lip and its existing finite back wall.

The native UV seam is posterior to two native quad rows. Preserve that wall's
measured cross-section instead of mistaking the seam for the visible front lip.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0108-visible-eyelid-rim';PRE=E.parent/'r0107-native-coarse-lid-cage'
sp=importlib.util.spec_from_file_location('r108lip',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def main():
 tick=time.time();save('finite-lip-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct native fine anterior lip and finite back-wall sculpt on the retained native hood.','newPremise':'Removing original Multires detail did not close the aperture; actual source row geometry places the UV seam posterior to the front lip.'});source=np.load(PRE/'native-coarse-lid-poses-pinned.npz');P0=source['neutralFineWorld'];T=source['fineTriangles'];data={k:source[k+'_fineDelta'].copy() for k in ['L_half','L_closed','R_half','R_closed']};diagnostic=json.loads((E/'visible-rim-causal-diagnostic.json').read_text('utf8'));rings=diagnostic['nativeQuadRows'];UV=np.load(E.parent/'r0105-native-head-skin-chart/actual-lip-and-native-chart.npz')['nativeUV-UVMap'];front=np.all((UV[:,:,1]>.5)&(UV[:,:,0]>.2)&(UV[:,:,0]<.8),1);external=np.zeros(len(P0),bool);external[np.unique(T[front])]=True;native=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');opt=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];C=np.mean([r['posteriorSphereFitCentreWorld'] for r in opt.values()],0);scale=np.linalg.norm(np.array(opt['L']['posteriorSphereFitCentreWorld'])-opt['R']['posteriorSphereFitCentreWorld'])/.060;arrays={'neutralFineWorld':P0,'fineTriangles':T};report={}
 for side in ['L','R']:
  rows=[np.array(r,dtype=int) for r in rings[side]['nativeRows']];assert len(rows)==3 and all(len(r)==40 for r in rows);rim=rows[-1];points=P0[rim];lo=int(points[:,0].argmin());hi=int(points[:,0].argmax());paths=[]
  for direction in [1,-1]:
   path=[lo]
   while path[-1]!=hi:path.append((path[-1]+direction)%len(rim))
   paths.append(path)
  upper=max(paths,key=lambda x:points[x,2].mean());lower=min(paths,key=lambda x:points[x,2].mean());lp=points[np.array(lower)[np.argsort(points[lower,0])]];EV=native['GEO-head_animation_realistic.sclera.'+side+'-world'];EV=(EV-C)*scale+C;ET=native['GEO-head_animation_realistic.sclera.'+side+'-triangles'];tree=BVHTree.FromPolygons(EV.tolist(),ET.tolist(),all_triangles=True);limits=[points.min(0),points.max(0)];free=external&(P0[:,0]>limits[0][0]-.006)&(P0[:,0]<limits[1][0]+.006)&(P0[:,2]>limits[0][2]-.005)&(P0[:,2]<limits[1][2]+.009);band=np.unique(np.concatenate(rows));free[band]=False;anchors=np.flatnonzero(~free)
  for label,value in [('half',.5),('closed',1.)]:
   old=P0+data[side+'_'+label];target=old.copy();miss=[]
   for j,vertex in enumerate(rim):
    if j in [lo,hi]:continue
    z=np.interp(points[j,0],lp[:,0],lp[:,2])+( .0001 if j in upper else -.0001);z=points[j,2]+value*(z-points[j,2]);hit,no,fi,distance=tree.ray_cast(Vector((points[j,0],EV[:,1].min()-.02,z)),Vector((0,1,0)))
    if hit is None:miss.append(j);continue
    anterior=np.array([points[j,0],hit.y-.0004,z])
    for row in rows:target[row[j]]=anterior+(P0[row[j]]-points[j])
   mesh=bpy.data.meshes.new('AFN108_FINE_LIP_'+side+'_'+label);mesh.from_pydata(old.tolist(),[],T.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);ob.hide_render=True;group=ob.vertex_groups.new(name='AFN108_FIXED_HOOD_AND_FINITE_LIP');group.add(anchors.tolist(),1.,'REPLACE');md=ob.modifiers.new('AFN108_EXISTING_FINE_HOOD_SCULPT','LAPLACIANDEFORM');md.vertex_group=group.name
   for x in bpy.context.selected_objects:x.select_set(False)
   ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.context.view_layer.update();result=bpy.ops.object.laplaciandeform_bind(modifier=md.name);assert 'FINISHED' in result;mesh.vertices.foreach_set('co',target.astype('f4').ravel());mesh.update();ob.update_tag();bpy.context.view_layer.update();d,W,TT=u.b.geom(ob);W=W.copy();softError=float(np.linalg.norm(W[band]-target[band],axis=1).max());W[anchors]=target[anchors].astype('f4');assert np.array_equal(W[band],target[band].astype('f4'));arrays[side+'_'+label+'_fineDelta']=W-P0;arrays[side+'_'+label+'_fineWorld']=W;report[side+'_'+label]={'anteriorLipVertices':len(rim),'existingFiniteWallRows':len(rows),'allSourceBandVerticesRetained':len(band),'bandTargetsExactAsStoredFloat32':True,'wallRestCrossSectionPreservedAtAuthoredTargets':True,'minimumNeutralWallRow0ToAnteriorDistanceM':float(np.linalg.norm(P0[rows[0]]-points,axis=1).min()),'softResultBandResidualBeforeExplicitPinM':softError,'fineMaximumMoveM':float(np.linalg.norm(W-P0,axis=1).max()),'rayMissNativeColumnsRetainedNotExcluded':miss,'guideFrontClearanceM':.0004,'guideUpperLowerFrontGapM':.0002,'finiteFacesSelfOrContinuousContactNotCertified':True};bpy.data.objects.remove(ob,do_unlink=True)
 mesh=bpy.data.meshes.new('AFN108_FINE_FINITE_LID_LIP_AUTHORING');mesh.from_pydata(P0.tolist(),[],T.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);ob.shape_key_add(name='Basis')
 for side in ['L','R']:
  for label in ['half','closed']:ob.shape_key_add(name='AFN108_AUTHORING_'+side+'_'+label).data.foreach_set('co',arrays[side+'_'+label+'_fineWorld'].astype('f4').ravel())
 ob.hide_render=True;ob['scope']='Native fine anterior lip and measured existing back-wall pose authoring. All source band vertices and source wall cross-section retained. Bake to the same full woman; neither contact nor anatomical/global closure accepted from targets alone.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'native-finite-lid-authoring.blend'),compress=True);np.savez_compressed(E/'native-finite-lid-poses.npz',**arrays);save('finite-lip-authoring.json',{'sourceReference':'Original Dan Ulrich native animation-head actual fine rows, anterior/posterior geometry and r107 per-pose data. Original Multires removal diagnostic leaves aperture open; original sculpt detail retained in production.','construction':'Sculpt actual anterior native row and transport the two existing back-wall rows by their measured rest vectors. Retain r107 native hood, explicitly preserve fixed outer pose and actual finite band targets. All40 source points in each of3 existing rows retained; no density/radius/step/weight scan.','poses':report,'sourceShapeAndR105LipChartProtectedAtNeutral':True,'notAnatomicalOrFiniteContactProof':True,'seconds':time.time()-tick});print('R108_FINE_FINITE_LID_LIP_AUTHORED',time.time()-tick,flush=True)
if __name__=='__main__':main()
