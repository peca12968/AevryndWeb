"""Author a native-chart lip registration, preserving actual geometry and shaders.

The original texture depicts an open mouth. Pair its visible upper/lower opening
contours with the artist head's actual external-to-internal UV seam. This is a
continuous chart construction, not another 3D nearest-vertex UV projection.
"""
from pathlib import Path
from collections import Counter,defaultdict
import bpy,numpy as np,json,importlib.util,time,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0105-native-head-skin-chart';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0104-b2-native-head-material-repair.blend';OUT=S/'aevrynd-female-next-r0105-a-native-lip-chart.blend'
sp=importlib.util.spec_from_file_location('r105build',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;u.v.E=E
def save(name,row):(E/name).write_text(json.dumps(row,indent=2)+'\n',encoding='utf8',newline='\n')
def main():
 tick=time.time();assert not OUT.exists();ref=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');chart=np.load(E/'actual-lip-and-native-chart.npz');T=ref['triangles'];P=ref['world'];UV=chart['nativeUV-UVMap'];front=np.all(UV[:,:,1]>.5,axis=1);edges=[]
 for fi in np.flatnonzero(front):
  for j,k in [(0,1),(1,2),(2,0)]:edges.append((tuple(sorted((int(T[fi,j]),int(T[fi,k])))),fi,j,k))
 counts=Counter(e[0] for e in edges);adj=defaultdict(list);uvByID={}
 for key,fi,j,k in edges:
  pp=P[list(key)]
  if counts[key]!=1 or not np.all((pp[:,2]>1.38)&(pp[:,2]<1.41)&(abs(pp[:,0])<.04)&(pp[:,1]<-.11)):continue
  x,y=int(T[fi,j]),int(T[fi,k]);adj[x].append(y);adj[y].append(x);uvByID[x]=UV[fi,j];uvByID[y]=UV[fi,k]
 assert len(adj)>50 and all(len(v)==2 for v in adj.values()),'Actual original lip seam must form a closed chart boundary'
 left=min(adj,key=lambda i:uvByID[i][0]);right=max(adj,key=lambda i:uvByID[i][0]);arcs=[]
 for first in adj[left]:
  path=[left,first]
  while path[-1]!=right:
   nxt=[i for i in adj[path[-1]] if i!=path[-2]];assert len(nxt)==1 and nxt[0] not in path;path.append(nxt[0])
  arr=np.array([uvByID[i] for i in path]);arcs.append(arr[np.argsort(arr[:,0])])
 upper=max(arcs,key=lambda x:x[:,1].mean());lower=min(arcs,key=lambda x:x[:,1].mean());ul,ur=uvByID[left][0],uvByID[right][0]
 # Explicit authored texture landmarks from the unchanged source atlas preview.
 # UV y points are the external red lip boundaries around the dark oral image.
 tx=np.array([.385,.41,.45,.5,.55,.59,.615]);tu=np.array([.366,.380,.385,.386,.385,.380,.366]);tl=np.array([.366,.347,.340,.339,.340,.347,.366]);scale=.230/(ur-ul)
 bpy.ops.wm.open_mainfile(filepath=str(SRC));skin=bpy.data.objects['AFN104_COMPLETE_WOMAN_WITH_NATIVE_ANIMATION_HEAD'];raw=skin.data;d,V,TT=u.b.geom(skin);V=V.copy();TT=TT.copy();world=q.arr(raw.vertices,'co',len(raw.vertices),3);A=np.array(skin.matrix_world);world=world@A[:3,:3].T+A[:3,3];hf=q.arr(raw.attributes['AFN104_SourceHeadFace'].data,'value',len(raw.polygons),dtype='i4');starts=q.arr(raw.polygons,'loop_start',len(raw.polygons),dtype='i4');nums=q.arr(raw.polygons,'loop_total',len(raw.polygons),dtype='i4');ids=q.arr(raw.loops,'vertex_index',len(raw.loops),dtype='i4');layer=raw.uv_layers['VitruvianUV.UDIM'];old=q.arr(layer.data,'uv',len(layer.data),2);new=old.copy();nativeLayer=raw.uv_layers.new(name='AFN105_ORIGINAL_NATIVE_HEAD_CHART');native=np.zeros_like(old);changed=[]
 # R104 used a uniform IPD registration; reproduce it, without changing shape.
 optical=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text())['eyes'];centres=np.array([optical[s]['posteriorSphereFitCentreWorld'] for s in ['L','R']]);centre=centres.mean(0);P=(P-centre)*(np.linalg.norm(centres[0]-centres[1])/.060)+centre
 for face in np.flatnonzero(hf>=0):
  fi=hf[face];loops=np.arange(starts[face],starts[face]+nums[face]);pts=world[ids[loops]];p=P[T[fi]];a=p[1]-p[0];b=p[2]-p[0];D=np.column_stack((a,b));xy=np.linalg.lstsq(D,(pts-p[0]).T,rcond=None)[0].T;weights=np.c_[1-xy.sum(1),xy];native[loops]=weights@UV[fi]
  if not front[fi]:continue
  uv=native[loops];x=uv[:,0];y=uv[:,1];upperV=np.interp(x,upper[:,0],upper[:,1]);lowerV=np.interp(x,lower[:,0],lower[:,1]);isUpper=y>=(upperV+lowerV)/2;targetU=.5+(x-(ul+ur)/2)*scale;targetV=np.where(isUpper,np.interp(targetU,tx,tu)+(y-upperV)*scale,np.interp(targetU,tx,tl)+(y-lowerV)*scale)
  # Full authored lip region, then smooth blend in surrounding external skin.
  aWeight=np.clip((.075-abs(x-.5))/.030,0,1);bWeight=np.clip((.041-abs(y-.648))/.019,0,1);weight=aWeight*bWeight;weight=weight*weight*(3-2*weight);new[loops]=old[loops]*(1-weight[:,None])+np.c_[targetU,targetV]*weight[:,None]
  if np.any(weight>0):changed.extend(loops[weight>0].tolist())
 layer.data.foreach_set('uv',new.astype('f4').ravel());nativeLayer.data.foreach_set('uv',native.astype('f4').ravel());raw.uv_layers.active=layer;layer.active_render=True;raw.update();skin.update_tag();bpy.context.view_layer.update();dd,V2,T2=u.b.geom(skin);assert np.array_equal(V,V2) and np.array_equal(TT,T2)
 save('a-native-chart-authoring.json',{'source':str(SRC),'output':str(OUT),'authoringUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'construction':'Actual native external lip UV boundary split into its two original arcs; explicit anatomical registration to unchanged texture opening contours; smooth native-chart exterior registration. No nearest-point domain/vertex re-projection.','nativeBoundaryVertices':len(adj),'nativeUpperArc':upper.tolist(),'nativeLowerArc':lower.tolist(),'sourceTextureContourU':tx.tolist(),'sourceTextureUpperContourV':tu.tolist(),'sourceTextureLowerContourV':tl.tolist(),'nativeToTextureChartScale':float(scale),'changedLoops':len(changed),'maximumUVLoopChange':float(np.linalg.norm(new-old,axis=1).max()),'worldGeometryTopologyShadersTexturesMaterialsHairLashesLightsExposureUnchanged':True,'newSkinStillStatic':True,'notCapturedAnatomicalTexture':True,'secondsBeforePreview':time.time()-tick})
 skin['AFN105_scope']='Native-chart semantic upper/lower lip registration. Original head/body geometry, skin shaders/textures and groom unchanged. Static skin, native optical intersections and all unqualified operations/contacts/runtime remain unaccepted.';u.m.m.rig.shade.settings();u.m.m.rig.k.b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','body-face','profile']:views.append(u.v.image('a-native-lip-chart',view));save('a-view-controls.json',views)
 print('R105_A_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
