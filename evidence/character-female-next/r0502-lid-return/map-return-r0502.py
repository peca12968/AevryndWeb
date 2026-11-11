"""Trace return wall components and their boundaries on the evaluated source."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import numpy as np

ROOT=Path(__file__).resolve().parent


def edges(ring):
    return [tuple(sorted((a,b))) for a,b in zip(ring,ring[1:]+ring[:1])]


def partition(graph):
    visited=set()
    components=[]
    for seed in graph:
        if seed in visited:
            continue
        active=[seed]
        visited.add(seed)
        group=set()
        while active:
            i=active.pop()
            group.add(i)
            for j in graph[i]-visited:
                visited.add(j)
                active.append(j)
        components.append(group)
    return sorted(components,key=len,reverse=True)


def chart_faces(rings,materials):
    return_faces={int(id) for id in rings if materials[id]==0}
    edge_faces=defaultdict(list)
    graph={id:set() for id in return_faces}
    for i,ring in rings.items():
        for edge in edges(ring):
            edge_faces[edge].append(int(i))
    for fs in edge_faces.values():
        both=set(fs)&return_faces
        for i in both:
            graph[i].update(both-{i})
    return partition(graph),edge_faces


def boundary(component, edge_faces):
    edge_kinds={e:('skin' if set(fs)-component else 'opening')
        for e,fs in edge_faces.items() if len(set(fs)&component)==1}
    link=defaultdict(set)
    for a,b in edge_kinds:
        link[a].add(b)
        link[b].add(a)
    return edge_kinds,link


def main():
    data=json.loads((ROOT/'return-topology.json').read_text())
    groups, ef=chart_faces(data['rings'],data['faceMaterials'])
    with np.load(ROOT/'return-topology.npz',allow_pickle=False) as bank:
        points=bank['0/skin']
        ids=bank['ids']
        all_roots=set(bank['tri'].ravel().tolist())
        print('Components',len(groups))
        for c in groups:
            edges0,link=boundary(c,ef)
            loops=partition(link)
            verts=np.array(sorted({v for i in c for v in data['rings'][str(i)]}))
            v=points[np.searchsorted(ids,verts)]
            hits=set(data['witnesses'])&{str(f) for f in c}
            print('component',len(c),'min,max',min(c),max(c),'vertices',len(v),'centre',np.round(v.mean(0)*1000,3).tolist(),'loop lengths',[len(x) for x in loops],
                 'edges',Counter(edges0.values()),'valences',Counter(len(row) for row in link.values()),'witness',sorted(hits),'anchors',len(set(verts)&all_roots))
            for loop in loops[:5]:
                ll=sorted(loop)
                q=points[np.searchsorted(ids,ll)]*1000
                print('  loop',len(ll),'bounds',np.round(q.min(0),2),np.round(q.max(0),2),'skin anchors',len(loop&all_roots))
        for key,row in data['witnesses'].items():
            print('witness',key,'neutral/closed',np.round(np.array(row['neutral'])*1000,3).tolist(),np.round(np.array(row['closed'])*1000,3).tolist())
if __name__=='__main__':
    main()

