"""Compare exact authoring root distributions, not image opacity or realism."""
import json,hashlib
from pathlib import Path
import numpy as np
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0014-scalp-flow'
rows={}
for name,path in [('r0013',S/'aevrynd-female-next-r0013-b-native-hair-data.npz'),('r0014',S/'aevrynd-female-next-r0014-a-hair-data.npz')]:
    d=np.load(path);P=d['positions'][d['offsets'][:-1]];main=P[d['layers']<2];upper=main[main[:,2]>1.52];table=[]
    for y0,y1 in zip(np.arange(-.10,.02,.02),np.arange(-.08,.04,.02)):
        q=upper[(upper[:,1]>=y0)&(upper[:,1]<y1)];left=q[q[:,0]<0];right=q[q[:,0]>0];a=float(-left[:,0].max()) if len(left) else None;b=float(right[:,0].min()) if len(right) else None
        table.append({'yRangeM':[float(y0),float(y1)],'upperRootCount':len(q),'leftMinAbsXM':a,'rightMinAbsXM':b,'nearestLeftRightRootSeparationM':a+b if a is not None and b is not None else None})
    values=[q['nearestLeftRightRootSeparationM'] for q in table if q['nearestLeftRightRootSeparationM'] is not None]
    rows[name]={'cacheSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'primaryAndClumpRootCount':len(main),'aboveZ1_52RootCount':len(upper),'partRows':table,'medianNearestLeftRightRootSeparationM':float(np.median(values)) if values else None}
result={'scope':'Exact authoring-cache roots for primary/clump layers, above z 1.52 m, fixed 20 mm y bins. This is root-domain separation, not rendered part width, coverage opacity or an objective realism score. All bins are retained including missing-side results.','models':rows}
(E/'root-distribution-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
