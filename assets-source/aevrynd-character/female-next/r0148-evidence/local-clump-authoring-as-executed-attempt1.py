"""Native local open-tress guide layers; no whole-style/follicle inference."""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0148-native-groom-foundation';P=R/'Evidence/character-female-next/r0130-artist-native-groom/current-hair-native-triangle-charts.npz'
def main():
 x=np.load(P);V=x['world'];F=x['triangles'];UV=x['triangleUV'];C=x['componentLabels'];layers=[4490,54191,50917];guides=[];rows=[];uvals=np.linspace(.03,.97,9);tvals=np.linspace(.012,.988,97)
 for component in layers:
  ids=np.flatnonzero(C[F[:,0]]==component);uv=UV[ids].astype('f8');W=V[F[ids]].astype('f8');lo=uv.min((0,1));hi=uv.max((0,1));A=uv[:,1]-uv[:,0];B=uv[:,2]-uv[:,0];det=A[:,0]*B[:,1]-A[:,1]*B[:,0];assert (det<0).all(),'This selected local chart must have one consistent open surface orientation';lineage=[]
  for u in uvals:
   Q=[];anchors=[]
   for t in tvals:
    p=lo+np.array([u,t])*(hi-lo);q=p-uv[:,0];s=(q[:,0]*B[:,1]-q[:,1]*B[:,0])/det;r=(A[:,0]*q[:,1]-A[:,1]*q[:,0])/det;hit=np.flatnonzero((s>=-1e-8)&(r>=-1e-8)&(s+r<=1+1e-8));assert len(hit)>0,(component,u,t,'not a covered open surface path');j=int(hit[0]);bc=np.array([1-s[j]-r[j],s[j],r[j]]);Q.append(bc@W[j]);anchors.append([int(ids[j]),*bc])
   Q=np.array(Q);assert np.linalg.norm(Q[-1]-Q[0])>.1 and np.linalg.norm(np.diff(Q,axis=0),axis=1).max()<.015;guides.append(Q);lineage.append(anchors)
  rows.append({'component':component,'uvBounds':[lo.tolist(),hi.tolist()],'selectedTriangles':len(ids),'allUVTriangleOrientationNegative':True,'openPathNotClosedContour':True,'sourceTriangleBarycentric':lineage})
 Pts=np.array(guides);d=bpy.data.hair_curves.new('AFN148_LOCAL_OPEN_TRESS_GUIDE_DATA');d.add_curves([97]*len(Pts));d.position_data.foreach_set('vector',Pts.astype('f4').ravel());ob=bpy.data.objects.new('AFN148_EDITABLE_LOCAL_OPEN_TRESS_GUIDES',d);bpy.context.scene.collection.objects.link(ob)
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();np.savez_compressed(E/'local-clump-guides.npz',guides=Pts,layers=np.array(layers),u=uvals,t=tvals,sourceWorld=V,sourceTriangles=F,sourceComponentLabels=C)
 bpy.data.libraries.write(str(E/'local-clump-guide-component.blend'),{ob},fake_user=True)
 (E/'local-clump-guide-authoring.json').write_text(json.dumps({'UTC':now,'originalStartedUTC':'2026-10-22T03:17:50+00:00','action':'Author27 actual native editable3D open-tress curves over three verified original continuous left-front surface layers. This is one local replacement construction, not470 component medials, whole-head UV contours or a global style field.','layers':rows,'guides':27,'pointsPerGuide':97,'sourceCache':str(P),'noFollicleOrRootToScalpQualificationClaim':True,'continuationStartsNotBiologicalRoots':True,'componentOnlyNotCompleteWomanOrImprovement':True,'nativeComponent':str(E/'local-clump-guide-component.blend')},indent=2)+'\n',encoding='utf-8');print('R148_NATIVE_LOCAL_OPEN_TRESS_COMPONENT_AUTHORED',now,flush=True)
if __name__=='__main__':main()
