"""Cut the actual56 nonmanifold material seams to find native socket disks."""
from pathlib import Path
import numpy as np,collections,json,time
E=Path(r'D:\Download\Aevrynd\Evidence\character-female-next\r0060-ocular-assembly')
def main():
    tick=time.time();raw=np.load(E/'native-component-lineage.npz');corners=raw['corners'];starts=np.r_[0,np.cumsum(raw['polygonCounts'])];faces=[corners[starts[i]:starts[i+1]].tolist() for i in range(len(starts)-1)];mat=raw['materials'];P=raw['AFN57_Supplied_Female_Morph'];edges=collections.defaultdict(list)
    for i,f in enumerate(faces):
        for x,y in zip(f,f[1:]+f[:1]):edges[tuple(sorted((x,y)))].append(i)
    seams={e for e,ff in edges.items() if 7 in mat[ff] and 4 in mat[ff]};adj=collections.defaultdict(list)
    for edge,ff in edges.items():
        if edge in seams:continue
        skin=[i for i in ff if mat[i] in (1,4,5)]
        for i in skin:adj[i].extend(j for j in skin if j!=i)
    seen=set();groups=[]
    for seed in np.flatnonzero(np.isin(mat,(1,4,5))):
        if int(seed) in seen:continue
        group=[];todo=[int(seed)];seen.add(int(seed))
        while todo:
            j=todo.pop();group.append(j)
            for z in adj[j]:
                if z not in seen:seen.add(z);todo.append(z)
        vs=np.unique([v for j in group for v in faces[j]]);row={'faces':sorted(group),'vertices':vs.tolist(),'bounds':[P[vs].min(0).tolist(),P[vs].max(0).tolist()]};groups.append(row);print('R60_SKIN_DISK',len(group),len(vs),row['bounds'],flush=True)
    (E/'native-socket-patches.json').write_text(json.dumps({'seams':[list(e) for e in sorted(seams)],'groups':groups,'seconds':time.time()-tick},indent=2)+'\n',encoding='utf8');print('R60_SKIN_DISKS_READY',len(groups),time.time()-tick,flush=True)
if __name__=='__main__':main()
