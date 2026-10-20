"""One coherent native rest-lid aperture sculpture with actual lash-root frames.
New explicitly authored rim arcs; source blink only fades the sculpt to zero
at its original closed endpoint. Not a partial blink or crease coefficient.
"""
from pathlib import Path
from collections import defaultdict
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0088-lid-aperture';SRC=S/'aevrynd-female-next-r0081-b-stable-frame-curly-study.blend';OUT=S/'aevrynd-female-next-r0088-a-authored-lid-aperture.blend'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('r88source','build-female-next-r0081-editable-curly.py');q=m.q;v=module('r88views','render-female-next-r0081-retained-study.py');v.E=E
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sculpt_key(o,name,worldDelta,ctrl,side):
 A=np.array(o.matrix_world);delta=worldDelta@np.linalg.inv(A[:3,:3]).T;basis=q.arr(o.data.shape_keys.key_blocks[0].data,'co',len(o.data.vertices),3);key=o.shape_key_add(name=name,from_mix=False);key.relative_key=o.data.shape_keys.key_blocks[0];key.data.foreach_set('co',(basis+delta).astype('f4').ravel());key.slider_min=0;key.slider_max=1;fc=key.driver_add('value');fc.driver.type='SCRIPTED';fc.driver.expression='e*(1-v)'
 for label,obj,path in [('e',ctrl,'["sculpt_enabled"]'),('v',bpy.data.objects['AFN59_FACE_CONTROLS'],'["blink_'+('left' if side=='L' else 'right')+'"]')]:
  var=fc.driver.variables.new();var.name=label;var.type='SINGLE_PROP';var.targets[0].id=obj;var.targets[0].data_path=path
 assert fc.driver.is_simple_expression;return key.name,delta
def arcs(rim,seams,P):
 adj=defaultdict(list);selected=set(rim)
 for a,b in seams:
  if a in selected and b in selected:adj[a].append(b);adj[b].append(a)
 assert set(adj)==selected and all(len(x)==2 for x in adj.values());inner=min(rim,key=lambda i:abs(P[i,0]));outer=max(rim,key=lambda i:abs(P[i,0]));paths=[]
 for first in adj[inner]:
  path=[inner,first]
  while path[-1]!=outer:
   prev,here=path[-2:];nxt=next(x for x in adj[here] if x!=prev);assert nxt not in path;path.append(nxt)
  paths.append(path)
 paths.sort(key=lambda p:float(np.mean(P[p,2])),reverse=True);return inner,outer,paths
def harmonic(adj,rim,values,P,sign):
 active=set(rim);front=set(rim)
 for step in range(4):
  nxt={j for i in front for j in adj[i] if .012<P[j,0]*sign<.048 and 1.438<P[j,2]<1.486 and P[j,1]<-.09}-active;active|=nxt;front=nxt
 fixed=set(rim);unknown=sorted(active-fixed);idx={i:j for j,i in enumerate(unknown)};L=np.zeros((len(unknown),len(unknown)));B=np.zeros((len(unknown),3))
 for i in unknown:
  row=idx[i];L[row,row]=len(adj[i])
  for j in adj[i]:
   if j in idx:L[row,idx[j]]-=1
   elif j in fixed:B[row]+=values[j]
 solution=np.linalg.solve(L,B);delta=np.zeros_like(P)
 for i in rim:delta[i]=values[i]
 delta[unknown]=solution;return delta
def frame(T):
 a=T[1]-T[0];a/=np.linalg.norm(a);n=np.cross(a,T[2]-T[0]);n/=np.linalg.norm(n);return np.column_stack((a,np.cross(n,a),n))
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='dfcc38df12c6bd93c9659b90f8b665e973b7a90f3828b134297bd6f2365898c0';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();ctrl=bpy.data.objects.new('AFN88_LID_APERTURE_CONTROLS',None);s.collection.objects.link(ctrl);ctrl['sculpt_enabled']=1.;ctrl.id_properties_ui('sculpt_enabled').update(min=0.,max=1.,description='Native authored rest aperture and paired lash-frame sculpt; zero exactly restores the original source. Blink endpoints still require new affected checks.');body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];ref=np.load(E/'actual-native-margin-data.npz');P=ref['nativeWorld'];ids=ref['bodyNativeIDs'];lookup={int(i):j for j,i in enumerate(ids)};nativeSeams=json.loads((E.parent/'r0060-ocular-assembly/native-socket-patches.json').read_text())['seams'];seams=[(lookup[int(a)],lookup[int(b)]) for a,b in nativeSeams];rim=ref['rimLocalIndices'];adj=defaultdict(set)
 for f in body.data.polygons:
  vv=list(f.vertices)
  for a,b in zip(vv,vv[1:]+vv[:1]):adj[a].add(b);adj[b].add(a)
 # Actual render-level source triangles are the attachment reference.
 for md in body.modifiers:
  if md.type=='SUBSURF':md.levels=md.render_levels
 bpy.context.view_layer.update();skin=bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'];before=m.rig.k.mesh(skin);V0=before['V'].copy();T0=before['T'].copy();skinTree=BVHTree.FromPolygons(V0.tolist(),T0.tolist(),all_triangles=True);helper=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];H0=q.geom(helper)[1].copy();curves=bpy.data.objects['AFN57_NATIVE_LASHES'];counts=np.array([c.points_length for c in curves.data.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];deltas={};rows=[];arrays={};hair0=q.hair(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES']).copy()
 for sign,side in ((1,'L'),(-1,'R')):
  rr=[int(i) for i in rim if P[i,0]*sign>0];inner,outer,paths=arcs(rr,seams,P);values={i:np.zeros(3) for i in rr};optic=m.rig.k.mesh(bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX']);tree=BVHTree.FromPolygons(optic['V'].tolist(),optic['T'].tolist(),all_triangles=True);targets=[]
  for branch,path in enumerate(paths):
   for i in path[1:-1]:
    u=float((abs(P[i,0])-abs(P[inner,0]))/(abs(P[outer,0])-abs(P[inner,0])));u=float(np.clip(u,0,1));baseZ=(1-u)*P[inner,2]+u*P[outer,2];height=(.0048*(1+.12*(.5-u))) if branch==0 else (-.0021*(1-.15*(.5-u)));target=P[i].copy();target[2]=baseZ+height*4*u*(1-u);hitOld=tree.ray_cast(Vector((P[i,0],-.2,P[i,2])),Vector((0,1,0)))[0];hitNew=tree.ray_cast(Vector((target[0],-.2,target[2])),Vector((0,1,0)))[0]
    if hitOld is not None and hitNew is not None:target[1]+=float(hitNew.y-hitOld.y)
    values[i]=target-P[i];targets.append({'localVertex':i,'nativeVertex':int(ids[i]),'branch':'upper' if branch==0 else 'lower','u':u,'targetWorld':target.tolist(),'deltaWorld':values[i].tolist()})
  delta=harmonic(adj,rr,values,P,sign);assert max(np.linalg.norm(delta,axis=1))<.004,'Predeclared four-mm sculpture bound';assert np.array_equal(delta[[inner,outer]],np.zeros((2,3)));key,local=sculpt_key(body,'AFN88_'+side+'_REST_MARGIN_ARCS',delta,ctrl,side);deltas[side]=delta;arrays[side+'_bodyLocalDelta']=local;arrays[side+'_bodyWorldDelta']=delta;rows.append({'side':side,'shapeKey':key,'innerCanthusNativeID':int(ids[inner]),'outerCanthusNativeID':int(ids[outer]),'upperArcNativeIDs':ids[paths[0]].tolist(),'lowerArcNativeIDs':ids[paths[1]].tolist(),'explicitRimTargets':targets,'changedNativeVertices':int((np.linalg.norm(delta,axis=1)>1e-10).sum()),'maximumAuthoredWorldMoveM':float(np.linalg.norm(delta,axis=1).max()),'artDirectedUpperHeightM':.0048,'artDirectedLowerHeightM':.0021,'notUniversalAnatomicalMeasurement':True})
 bpy.context.view_layer.update();after=m.rig.k.mesh(skin);V1=after['V'];assert np.array_equal(after['T'],T0) and V1.shape==V0.shape;helperDelta={side:np.zeros_like(H0) for side in ('L','R')};bindings=[]
 for ci,(st,n) in enumerate(zip(starts,counts)):
  st=int(st);n=int(n);root=H0[st];co,_,face,gap=skinTree.find_nearest(Vector(root));tri=T0[face];bary=m.rig.base.bary(np.array(co),V0[tri]);anchor0=bary@V0[tri];anchor1=bary@V1[tri];rotation=frame(V1[tri])@frame(V0[tri]).T;Q=(H0[st:st+n]-anchor0)@rotation.T+anchor1;side='L' if root[0]>0 else 'R';helperDelta[side][st:st+n]=Q-H0[st:st+n];bindings.append({'curve':ci,'side':side,'triangle':tri.tolist(),'barycentric':bary.tolist(),'sourceRootDistanceM':float(gap),'rootWorldMoveM':float(np.linalg.norm(Q[0]-root))})
 for side in ('L','R'):
  key,local=sculpt_key(helper,'AFN88_'+side+'_REST_LASH_FRAMES',helperDelta[side],ctrl,side);arrays[side+'_lashHelperLocalDelta']=local;arrays[side+'_lashHelperWorldDelta']=helperDelta[side]
 bpy.context.view_layer.update();hairError=float(np.linalg.norm(q.hair(bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'])-hair0,axis=1).max());assert hairError<2e-6;arrays['sourceHelperNeutralWorld']=H0;arrays['sourceSkinNeutralWorld']=V0;arrays['sourceSkinTriangles']=T0;arrays['authoredSkinNeutralWorld']=V1;np.savez_compressed(E/'a-native-aperture-lineage.npz',**arrays);save('a-lash-root-bindings.json',bindings);m.rig.shade.settings();s.render.hair_subdiv=3;m.rig.k.b.camera('face');s.camera.data.lens=85;s['AFN88_scope']='Art-directed native upper/lower rest-margin arcs with actual evaluated-skin lash frames, source closed endpoint through zero fade. No new blink/contact/natural-motion/runtime acceptance.';ctrl['scope']=s['AFN88_scope'];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'control':ctrl.name,'construction':rows,'sourceClosedEndpointFade':'New keys use enabled*(1-blink); original open/closed keys and sampled source quarter poses untouched. Exact closed display and intermediate contact need independent proof.','lashCurves':len(counts),'lashPoints':int(counts.sum()),'lashBinding':'Actual source render-skin triangle/barycentric frame transported to the sculpted render-skin, per curve; original radii and topology retained. No new follicles or physical dynamics claimed.','neutralMainHairMaximumWorldErrorM':hairError,'sourceOpticalGeometrySkinMaterialsLightsUnedited':True,'secondsBeforePreview':time.time()-tick,'contactBlinkNaturalDynamicsRuntimeAccepted':False});renders=[]
 for view in ('face','body-face','oblique'):renders.append(v.image('a-aperture',view));save('a-pilot-controls.json',renders)
 print('R88_NATIVE_LID_APERTURE_PILOT_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
