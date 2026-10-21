"""Bounded actual current ocular layer/pivot evidence, no source/control substitution."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0138-native-current-gaze';SRC=R/'engine/assets/characters/female-next/source/r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'
sp=importlib.util.spec_from_file_location('r138inspectbase',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b
def fit(P):
 c=np.linalg.lstsq(np.c_[2*P,np.ones(len(P))],np.sum(P*P,axis=1),rcond=None)[0];center=c[:3];r=float(np.sqrt(c[3]+center@center));res=np.linalg.norm(P-center,axis=1)-r;return {'center':center.tolist(),'radiusM':r,'maxAbsResidualM':float(abs(res).max()),'rmsResidualM':float(np.sqrt((res*res).mean())),'vertices':len(P)}
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));rows=[]
 for name in ['AFN126_ORIGINAL_Eye_Eye_0','AFN126_ORIGINAL_EyeScleraReflect_EyeScleraReflect_0','AFN126_ORIGINAL_MeniscusEyeSpec_MeniscusEye_0','AFN126_ORIGINAL_Eyelashes_Eyelashes_0']:
  o=bpy.data.objects[name];_,W,T=b.u.b.geom(o);side={}
  for label,mask in [('L',W[:,0]>0),('R',W[:,0]<0)]:
   P=W[mask];mid=(P[:,1].min()+P[:,1].max())*.5;rear=P[P[:,1]>mid];side[label]={'bounds':[P.min(0).tolist(),P.max(0).tolist()],'fullFit':fit(P),'posteriorFit':fit(rear),'posteriorNativeVertexIds':np.flatnonzero(mask)[P[:,1]>mid].tolist()}
  rows.append({'name':name,'visible':not o.hide_render,'rawVertices':len(o.data.vertices),'evaluatedVertices':len(W),'triangles':len(T),'matrixWorld':np.array(o.matrix_world).tolist(),'meshUsers':o.data.users,'modifiers':[(m.name,m.type) for m in o.modifiers],'vertexGroups':[g.name for g in o.vertex_groups],'uvMaps':[u.name for u in o.data.uv_layers],'sideCrossingTriangles':int(((W[T,0].min(1)<0)&(W[T,0].max(1)>0)).sum()),'sides':side})
 out={'source':str(SRC),'sourceSha256':a.sha(SRC),'frontDirection':'world -Y; anatomical L world+X, R world-X','movingLayers':['AFN126_ORIGINAL_Eye_Eye_0','AFN126_ORIGINAL_EyeScleraReflect_EyeScleraReflect_0'],'fixedLayers':['skin/eyelids','meniscus tear film','eyelashes'],'posteriorSphereFitIsPivotConstructionNotFullOpticalOrContactProof':True,'actualNativeLayers':rows,'seconds':time.time()-tick};(E/'actual-current-optical-layers.json').write_text(json.dumps(out,indent=2)+'\n');print('R138_ACTUAL_CURRENT_NATIVE_OPTICAL_LAYERS_READ',[(r['name'],r['evaluatedVertices'],{s:{k:x for k,x in v['posteriorFit'].items() if k!='vertices'} for s,v in r['sides'].items()}) for r in rows],flush=True)
if __name__=='__main__':main()
