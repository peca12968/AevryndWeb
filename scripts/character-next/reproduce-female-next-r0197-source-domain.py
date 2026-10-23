"""Independent saved-data reproduction of failed source scalp domains.
This is a source-construction diagram, not a new complete-character result.
"""
from pathlib import Path
import numpy as np,json,datetime,hashlib,ast
from PIL import Image,ImageDraw,ImageFont
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0197-anatomical-scalp-reconstruction';b=E/'build-unavailable'
src=np.load(E/'original-full-native-groom-data.npz');original=np.load(E/'original-source-cap-domain.npz');V=src['sourceBodyWorld'].astype('f8');T=src['sourceBodyTriangles'];owners=src['sourceOwnerFaces'];mask=original['sourceSelectedMask'].copy();script=C/'scripts/character-next/build-female-next-r0197-anatomical-scalp.py';tree=ast.parse(script.read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fill_holes');ns={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(script),'exec'),ns);mask=ns['fill_holes'](T,mask,V)
_,pid=np.unique(np.round(V,6),axis=0,return_inverse=True);F=pid[T];repairs=[]
for _ in range(3):
 ed=np.sort(np.vstack([F[mask][:,[0,1]],F[mask][:,[1,2]],F[mask][:,[2,0]]]),axis=1);ed,c=np.unique(ed,axis=0,return_counts=True);ed=ed[c==1];ids,degree=np.unique(ed,return_counts=True);bad=ids[degree>2]
 if not len(bad):break
 extra=np.any(np.isin(F,bad),axis=1)&~mask;repairs.append({'geometricPositionIDs':bad.tolist(),'sourceFacesAdded':np.flatnonzero(extra).tolist()});mask=ns['fill_holes'](T,mask|extra,V)
assert not len(bad)
adj={}
for x,y in ed:adj.setdefault(int(x),[]).append(int(y));adj.setdefault(int(y),[]).append(int(x))
unseen=set(adj);loops=[]
while unseen:
 start=min(unseen);walk=[start];prev=None;current=start
 while True:
  nxt=next(x for x in adj[current] if x!=prev)
  if nxt==start:break
  assert nxt not in walk;walk.append(nxt);prev,current=current,nxt
 unseen.difference_update(walk);loops.append(walk)
assert sorted(map(len,loops))==[3,6,87]
selected=np.flatnonzero(mask);parent=np.arange(len(T));edgeFirst={}
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for fi in selected:
 for a,b in [(0,1),(1,2),(2,0)]:
  edge=tuple(sorted((int(F[fi,a]),int(F[fi,b]))))
  if edge in edgeFirst:parent[find(int(fi))]=find(edgeFirst[edge])
  else:edgeFirst[edge]=int(fi)
labels=np.array([find(int(fi)) for fi in selected]);labs,sizes=np.unique(labels,return_counts=True);order=labs[np.argsort(sizes)[::-1]];components=[];faceComponent=np.full(len(T),-1,'i4')
for ci,lab in enumerate(order):
 faces=selected[labels==lab];faceComponent[faces]=ci;points=V[np.unique(T[faces])];components.append({'component':ci,'sourceFaceCount':len(faces),'sourceFaceIDs':faces.tolist(),'worldBounds':np.stack([points.min(0),points.max(0)]).tolist(),'nearestFirstControlPointOwnerCurveCount':int(np.isin(owners,faces).sum())})
canonical=np.full(pid.max()+1,-1,'i4')
for i,k in enumerate(pid):
 if canonical[k]<0:canonical[k]=i
loopRecords=[{'vertices':len(loop),'actualSourceVertexIDs':canonical[loop].tolist(),'worldPositions':V[canonical[loop]].tolist()} for loop in loops]
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceInputs':{p.name:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in [E/'original-full-native-groom-data.npz',E/'original-source-cap-domain.npz',script]},'sameFailureIndependentlyReproducedFromSavedArrays':True,'sourcePositionAdjacencyDoesNotResolveRemainingLoops':True,'localPinchClosure':repairs,'regularBoundaryLoopSizes':sorted(map(len,loops)),'selectedFaceComponents':components,'boundaryLoops':loopRecords,'allNativeOwnerFacesRetained':bool(mask[owners].all()),'sourceGroupAndNearestFirstPointFaceUnionIsNotQualifiedAnatomicalBirthDomain':True,'firstPointOffsetsAreNotAProvenCauseOfEveryRootOrRenderIssue':True,'noCurrentSkinOrCandidateProduced':True,'noAdditionalConstructionOrRepairAttempt':True}
(E/'independent-source-domain-failure.json').write_bytes((json.dumps(q,indent=2)+'\n').encode())
colors=['#7497ae','#da7666','#c2a86d','#957ba9'];canvas=Image.new('RGB',(1440,600),'#f7f8fa');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);titleFont=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
draw.text((30,15),'FAILED SOURCE SCALP DOMAIN: 3 boundary loops (3 / 6 / 87 vertices)',fill='#202d3d',font=titleFont);draw.text((30,51),'Geometry-data diagnosis only; no new complete woman and no successful scalp join.',fill='#5f6976',font=font);pairings=[(0,2,'Front / X-Z'),(1,2,'Side / Y-Z'),(0,1,'Top / X-Y')]
for panel,(x,y,title) in enumerate(pairings):
 polys=V[T[selected]][:,:,[x,y]]*1000;lo=polys.reshape(-1,2).min(0);hi=polys.reshape(-1,2).max(0);ratio=min(400/(hi[0]-lo[0]),380/(hi[1]-lo[1]));origin=np.array([panel*480+35,115]);draw.text((panel*480+35,88),title,fill='#202d3d',font=font)
 def xy(p):z=(np.asarray(p)-lo)*ratio;return (float(origin[0]+z[0]),float(origin[1]+380-z[1]))
 for poly,fi in zip(polys,selected):draw.polygon([xy(p) for p in poly],fill=colors[min(faceComponent[fi],len(colors)-1)])
 for lr in loopRecords:
  P=V[lr['actualSourceVertexIDs']][:,[x,y]]*1000;P=np.vstack([P,P[0]]);draw.line([xy(p) for p in P],fill='#28323e',width=2)
 draw.text((panel*480+35,513),f'Width {(hi[0]-lo[0]):.1f} mm / height {(hi[1]-lo[1]):.1f} mm',fill='#5f6976',font=font)
draw.text((30,555),'Selected face components: '+', '.join(str(c['sourceFaceCount'])+' faces / '+str(c['nearestFirstControlPointOwnerCurveCount'])+' first-point owners' for c in components),fill='#202d3d',font=font);canvas.save(E/'failed-source-scalp-domain.png')
print('R197_SOURCE_DOMAIN_FAILURE_INDEPENDENTLY_REPRODUCED',json.dumps({'UTC':q['UTC'],'loopSizes':q['regularBoundaryLoopSizes'],'components':[{'faces':x['sourceFaceCount'],'nearestFirstPointOwnerCurves':x['nearestFirstControlPointOwnerCurveCount']} for x in components]}),flush=True)
