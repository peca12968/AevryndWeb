"""Bounded actual-fibre self-contact falsification at the intentional tie.

One cross-section can falsify all-hair separation, never prove global safety.
Interior segment/segment closest points below summed radii are witnesses for
the actual finite cylindrical shafts. No blanket acceptance of tie overlaps.
"""
from pathlib import Path
import numpy as np,json,math
E=Path(r'D:\Download\Aevrynd\Evidence\character-female-next\r0061-surface-flow-groom')

def main():
    raw=np.load(E/'b-fibres-authoring.npz');Q=raw['positions'].astype('f8');rr=raw['radii'].astype('f8');ref=json.loads((E/'b-fibres-build-summary.json').read_text());C=np.array(ref['route']['tieCentre']);step=float(rr.max()*2);grid={};pairs=0;interior=0;examples=[];crossings=0
    for ci,p in enumerate(Q):
        cut=np.flatnonzero((p[:-1,1]-C[1])*(p[1:,1]-C[1])<=0)
        if not len(cut):continue
        j=int(cut[0]);t=(C[1]-p[j,1])/(p[j+1,1]-p[j,1]);x=p[j]+t*(p[j+1]-p[j]);key=tuple(np.floor(x[[0,2]]/step).astype('i8'));r0=float(max(rr[ci,j:j+2]));crossings+=1
        for dx in (-1,0,1):
            for dz in (-1,0,1):
                for cj,k,xx,r1 in grid.get((key[0]+dx,key[1]+dz),[]):
                    if np.linalg.norm(x-xx)>=r0+r1:continue
                    pairs+=1;A=p[j];u=p[j+1]-A;B=Q[cj,k];v=Q[cj,k+1]-B;w=A-B;a=u@u;b=u@v;c=v@v;d=u@w;e=v@w;den=a*c-b*b
                    if abs(den)<1e-24:continue
                    s=(b*e-c*d)/den;t=(a*e-b*d)/den
                    if not(0<s<1 and 0<t<1):continue
                    distance=float(np.linalg.norm(A+s*u-B-t*v));actualR=float((1-s)*rr[ci,j]+s*rr[ci,j+1]+(1-t)*rr[cj,k]+t*rr[cj,k+1])
                    if distance>=actualR-1e-6:continue
                    interior+=1
                    if len(examples)<30:examples.append({'curves':[ci,cj],'segments':[j,k],'fractions':[float(s),float(t)],'shaftDistanceM':distance,'sumInterpolatedRadiiM':actualR,'overlapM':actualR-distance,'closestPointsM':[(A+s*u).tolist(),(B+t*v).tolist()]})
        grid.setdefault(key,[]).append((ci,j,x,r0))
    result={'source':ref['output'],'sha256':ref['outputSha256'],'status':'FAIL_ACTUAL_SHAFT_SELF_SEPARATION' if interior else 'NOT_FALSIFIED_IN_SINGLE_CUT_NOT_GLOBAL_PASS','method':'Tie-plane spatial hash then exact finite segment interior/interior closest points; distance below sum of actual interpolated radii minus1um. B and C geometry/radii must match before transferring evidence.','crossings':crossings,'cutClosePairs':pairs,'provenInteriorShaftPairs':interior,'examples':examples,'numericalAllowanceM':1e-6,'scope':'One tie plane only, not exhaustive whole hair, roots, dynamics or runtime. Intentional gathering does not authorize interpenetration.'}
    (E/'b-tie-self-falsification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(result['status'],crossings,pairs,interior)
if __name__=='__main__':main()
