"""Map neutral and posed contact findings back to persistent curves and scalp route ownership."""
from ast import literal_eval
from collections import Counter
from hashlib import file_digest
from pathlib import Path
import json
import struct
import zipfile

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'r0508-frontal-sweep'


def load(path):
    return json.loads(path.read_bytes())


def read_ints(archive,key):
    with archive.open(f'{key}.npy') as stream:
        assert stream.read(6)==b'\x93NUMPY'
        version=tuple(stream.read(2))
        assert version in ((1,0),(2,0),(3,0))
        width=2 if version[0]==1 else 4
        header=literal_eval(stream.read(int.from_bytes(stream.read(width),'little')).decode())
        assert header['descr']=='<i4' and len(header['shape'])==1
        value=[v for v, in struct.iter_unpack('<i',stream.read())]
        assert len(value)==header['shape'][0]
        return value


def main():
    build=load(ROOT/'construction-receipt.json')
    audit=load(ROOT/'skin-contact.json')
    old=load(PREVIOUS/'failure-location.json')
    old_build=load(PREVIOUS/'construction-receipt.json')
    assert build['source']==audit['source'] and build['comparisonSource']==old_build['parent'] and old['source']==old_build['source']
    old_ids={v['curveID'] for v in old['failedCurves']}
    assert len(old_ids)==10 and old_ids<=set(audit['persistentCurveIDs'])
    bank=Path(build['guideBank']['path'])
    with bank.open('rb') as handle:
        assert file_digest(handle,'sha256').hexdigest()==build['guideBank']['sha256']
    with zipfile.ZipFile(bank) as data:
        ids,layer,route,side=(read_ints(data,name) for name in ('curveIDs','layer','route','side'))
    lookup={cid:i for i,cid in enumerate(ids)}
    assert len(lookup)==len(ids)
    pinnae=load(PREVIOUS/'frontal-probe.json')['pinnae']
    findings={}
    for frame,pose in audit['poses'].items():
        f={}
        for mode,row in pose['modes'].items():
            failed=set(row['failedCurveIds'])
            by_route=Counter()
            for i in failed:
                j=lookup[i]
                assert layer[j]>=0 and route[j]>=0
                by_route[(side[j],layer[j],route[j])]+=1
            worst=row['mostNegativeFailedCurveSample']
            nearest=None
            if worst is not None and frame=='1':
                x,y,z=worst['positionMetres']
                ear=pinnae[1 if x>0 else 0]
                if ear['front']-.003<=y<=ear['back']+.003 and ear['bottom']-.003<=z<=ear['top']+.003:
                    nearest='Neutral witness lies within the measured ear-level fore/aft and vertical bounds with a 3 mm margin.'
                elif z>=1.49:
                    nearest='Neutral witness lies above 1.49 m on the measured head.'
                else:
                    nearest='Neutral witness lies below 1.49 m outside the measured ear-level bounds.'
            f[mode]=dict(failedCurveCount=len(failed),priorR508FailedCurveIdsStillFailing=sorted(old_ids&failed),
                         priorR508FailedCurveIdsWithoutConfirmedFailure=sorted(old_ids-failed),
                         byRoute=[dict(side=a,layer=b,route=c,failedCount=k) for (a,b,c),k in sorted(by_route.items())],
                         worstConfirmed=worst,neutralWitnessLocation=nearest,insideCentres=row['insideCentres'],
                         crossingChords=row['centrelineCrossingSegments'],unresolvedChords=row['unresolvedRadiusSegments'])
            print(frame,mode,len(failed),len(old_ids&failed),nearest,
                  (worst['signedOrBoundMetres']*1000. if worst else None))
        findings[frame]=f
    report=dict(source=build['source'],previousFailedSource=old['source'],
                earlierFailedCurveIDs=sorted(old_ids),poses=findings,
                scope='All ten r0508 witness identities belong to the sampled r0509 cohort. A curve without confirmed failure is scoped to the listed pose and finite-radius samples. Position ranges identify the anatomical neighbourhood.')
    (ROOT/'failure-location.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()

