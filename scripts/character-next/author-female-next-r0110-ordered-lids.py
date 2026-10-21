"""Author native lids through explicit upper/lower ordered quad-strip charts.

Preserve source vertex graph; reconstruct pose correspondence without a spatial
nearest-surface field, guessed three-row margin, globe projection or solver.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0110-ordered-lid-topology';PRE=E.parent/'r0107-native-coarse-lid-cage'
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def arc_parts(loop,V):
 lo=int(V[loop,0].argmin());hi=int(V[loop,0].argmax());parts=[]
 for direction in [1,-1]:
  path=[lo]
  while path[-1]!=hi:path.append((path[-1]+direction)%len(loop))
  parts.append(path)
 return {'upper':max(parts,key=lambda p:V[np.array(loop)[p],2].mean()),'lower':min(parts,key=lambda p:V[np.array(loop)[p],2].mean())}
def chart(loop,strips,V):
 lookup={tuple(sorted((int(a),int(b)))):row for (a,b),row in zip(zip(loop,np.roll(loop,-1)),strips)};parts=arc_parts(loop,V);result={}
 for part,path in parts.items():
  points=V[np.array(loop)[path]];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))];arc/=arc[-1];rows=[]
  for j in range(len(path)-1):
   a,b=loop[path[j]],loop[path[j+1]];row=lookup[tuple(sorted((a,b)))];edgeIDs=np.array([r['edge'] for r in row]);mid=V[edgeIDs].mean(1);length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(mid,axis=0),axis=1))];rim=int(mid[:,1].argmin());assert length[-1]>0
   t=np.empty(len(length));t[:rim+1]=(length[:rim+1]-length[rim])/max(length[rim],1e-8);t[rim:]=(length[rim:]-length[rim])/max(length[-1]-length[rim],1e-8);rows.append({'s':float((arc[j]+arc[j+1])/2),'t':t,'edgeIDs':edgeIDs,'rimRow':rim})
  result[part]=rows
 return result
def sample(rows,s,t,V):
 stations=np.array([r['s'] for r in rows]);right=int(np.searchsorted(stations,s));right=min(max(right,1),len(rows)-1);left=right-1;alpha=float(np.clip((s-stations[left])/(stations[right]-stations[left]),0,1));out=[]
 for row in [rows[left],rows[right]]:
  p=V[row['edgeIDs']].mean(1);out.append(np.array([np.interp(t,row['t'],p[:,k]) for k in range(3)]))
 return out[0]*(1-alpha)+out[1]*alpha
def main():
 tick=time.time()
 if not (E/'ordered-authoring-start.json').exists():save('ordered-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct ordered upper/lower quad-strip reconstruction across actual complete hood and short wall; fixed posterior cup face domain explicitly separate.'})
 native=np.load(PRE/'native-coarse-lid-poses-pinned.npz');P=native['neutralFineWorld'];T=native['fineTriangles'];artist=np.load(E.parent/'r0109-complete-native-lid-sheet/actual-artist-external-blink.npz');A=artist['neutralWorld'];assert all(np.array_equal(artist['neutralPolygonCounts'],artist[k+'PolygonCounts']) and np.array_equal(artist['neutralLoopVertexIndices'],artist[k+'LoopVertexIndices']) for k in ['half','closed']);top=json.loads((E/'ordered-native-artist-topology.json').read_text('utf8'));rings=json.loads((E.parent/'r0108-visible-eyelid-rim/visible-rim-causal-diagnostic.json').read_text('utf8'))['nativeQuadRows'];arrays={'neutralFineWorld':P,'fineTriangles':T};report={}
 for side in ['L','R']:
  nloop=rings[side]['nativeRows'][0];aloop=top['artistStrips'][side]['loop'];nc=chart(nloop,top['nativeStrips'][side],P);ac=chart(aloop,top['artistStrips'][side]['strips'],A);sx=np.ptp(P[nloop,0])/np.ptp(A[aloop,0]);sz=np.ptp(P[nloop,2])/np.ptp(A[aloop,2]);axis=np.array([sx,sx,sz]);sums={label:np.zeros_like(P) for label in ['half','closed']};weights=np.zeros(len(P));records=[]
  for part,rows in nc.items():
   for row in rows:
    for j,(edge,t) in enumerate(zip(row['edgeIDs'],row['t'])):
     original=sample(ac[part],row['s'],t,A);fade=1-(max(t,0)**2)*(3-2*max(t,0));fade=float(np.clip(fade,0,1))
     for label in sums:
      actual=sample(ac[part],row['s'],t,artist[label+'World']);delta=(actual-original)*axis*fade
      for vi in edge:sums[label][vi]+=delta
     for vi in edge:weights[vi]+=1
    records.append({'part':part,'station':row['s'],'nativeRimRowByActualAnteriorExtremum':row['rimRow'],'nativeOrderedEdges':row['edgeIDs'],'nativeWallAndHoodCoordinate':row['t']})
  selected=weights>0
  for label,total in sums.items():
   delta=np.zeros_like(P);delta[selected]=total[selected]/weights[selected,None];arrays[side+'_'+label+'_fineDelta']=delta;arrays[side+'_'+label+'_fineWorld']=P+delta
  report[side]={'explicitUpperLowerSeparateCharts':True,'nativeChartVertices':int(np.count_nonzero(selected)),'nativeExistingPolygonGraphPreserved':True,'posteriorCupInteriorExcludedFromMobileHeadChartByActualFaceComponent':True,'cupAndHeadFacesAfterCut':top['nativeComponentFacesAfterUVSeamCut'],'actualPerStationRimRows':[r['nativeRimRowByActualAnteriorExtremum'] for r in records],'sourceLandmarkAxisScale':axis,'maxClosedMoveM':float(np.linalg.norm(arrays[side+'_closed_fineDelta'],axis=1).max()),'charts':records,'finiteThicknessAnatomicalMarginSelfAndContactUnaccepted':True}
 mesh=bpy.data.meshes.new('AFN110_ORDERED_NATIVE_UPPER_LOWER_LID_AUTHORING');mesh.from_pydata(P.tolist(),[],T.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);ob.shape_key_add(name='Basis')
 for side in ['L','R']:
  for label in ['half','closed']:ob.shape_key_add(name='AFN110_AUTHORING_'+side+'_'+label).data.foreach_set('co',arrays[side+'_'+label+'_fineWorld'].astype('f4').ravel())
 ob.hide_render=True;ob['scope']='Existing source graph explicitly charted into separate upper/lower ordered quad strips, anterior extremum and short-wall coordinate, posterior cup face domain fixed. Derived actual artist external pose data under CC-BY4.0. No new base topology, global contact or natural closure accepted from authoring alone.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'ordered-native-lid-authoring.blend'),compress=True);np.savez_compressed(E/'ordered-native-lid-poses.npz',**arrays);save('ordered-native-lid-authoring.json',{'construction':'Explicit semantic upper/lower ordered quad-strip correspondence to inspected real artist external poses, measured anterior extrema separate wall/hood, fixed posterior cup domain. Reconstruct poses on original native graph; not spatial/nearest, no analytic closure/projection or Laplacian. Source graph unchanged, no claim of new retopologized base.','sourceArtist':'Blender Studio Ellie v1 / GEO-ellie_head / CC-BY4.0','actualArtistPoseDataTransferred':True,'poses':report,'seconds':time.time()-tick});print('R110_ORDERED_NATIVE_LIDS_AUTHORED',time.time()-tick,flush=True)
if __name__=='__main__':main()
