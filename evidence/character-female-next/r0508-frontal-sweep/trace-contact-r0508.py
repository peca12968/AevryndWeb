"""Attach the actual failed native curve IDs to their frontal guide ownership."""
from ast import literal_eval
from hashlib import file_digest
from pathlib import Path
import json
import struct
import zipfile

ROOT=Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT/name).read_bytes())


def npy_ints(archive,name):
    with archive.open(f'{name}.npy') as stream:
        assert stream.read(6)==b'\x93NUMPY'
        version=tuple(stream.read(2))
        assert version in ((1,0),(2,0),(3,0))
        width=2 if version[0]==1 else 4
        header=literal_eval(stream.read(int.from_bytes(stream.read(width),'little')).decode())
        assert header['descr']=='<i4' and len(header['shape'])==1
        rows=[v for v, in struct.iter_unpack('<i',stream.read())]
        assert len(rows)==header['shape'][0]
        return rows


def main():
    build=read('construction-receipt.json')
    contact=read('skin-contact.json')
    probe=read('frontal-probe.json')
    assert build['source']==contact['source'] and build['parent']==probe['source']
    path=Path(build['guideBank']['path'])
    with path.open('rb') as handle:
        assert file_digest(handle,'sha256').hexdigest()==build['guideBank']['sha256']
    with zipfile.ZipFile(path) as data:
        ids,layer,route,side=(npy_ints(data,name) for name in ('curveIDs','layer','route','side'))
    assert len(ids)==len(set(ids))
    rows={cid:i for i,cid in enumerate(ids)}
    pose=contact['poses']['1']
    result=pose['modes']['over_under']
    a=pose['modes']['side_sweep']
    baseline=pose['modes']['control']
    assert not a['failedCurveIds'] and not baseline['failedCurveIds']
    failed=result['newFailedCurveIds']
    assert failed==result['failedCurveIds']
    issue=[]
    for cid in failed:
        index=rows[cid]
        assert layer[index]>=0 and route[index]>=0
        witnesses=[v for v in result['crossingWitnesses'] if v['curveID']==cid]
        issue.append(dict(curveID=cid,headSide=side[index],layer='upper' if layer[index]==0 else 'ear-side',
                          frontalRoute=route[index],crossings=witnesses))
    ear=probe['pinnae'][1]
    worst=result['mostNegativeFailedCurveSample']
    x,y,z=worst['positionMetres']
    assert x>0 and ear['front']<=y<=ear['back'] and ear['bottom']<=z<=ear['top']
    report=dict(source=build['source'],frame=1,mode='over_under',
        target='Evaluated neutral woman skin',
        failedCurves=issue,insideSamples=result['insideCentres'],
        crossingChords=result['centrelineCrossingSegments'],
        unresolvedRadiusChords=result['unresolvedRadiusSegments'],
        minimumConfirmedSample=worst,
        matchingMeasuredPinnaBoundsMetres=ear,
        positionDescription='The most negative sample is on the positive-X side within the measured fore/aft and vertical bounds of the lower pinna. Exact coordinates are recorded; the nearest triangle was not classified by anatomical labels.')
    (ROOT/'failure-location.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('B failures:',[(v['curveID'],v['headSide'],v['layer'],v['frontalRoute']) for v in issue])
    print('Worst gap in mm:',worst['signedOrBoundMetres']*1000.)


if __name__=='__main__':
    main()

