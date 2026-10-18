"""Reference reconstruction controls before fitting oral assets to a character."""
import json,hashlib
from pathlib import Path
import numpy as np
import oral_proxy_data as p
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0024-oral-layers';D=S/'oral/makehuman-system-cc0';BASE=Path(r'C:\Users\USER\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\mpfb\data\3dobjs\base.obj')
def main():
    body,uv,f,fu=p.obj(BASE);rows=[]
    for folder,stem in ((D/'teeth/teeth_base','teeth_base'),(D/'tongue/tongue01','tongue01')):
        mesh=folder/(stem+'.obj');mapping=folder/(stem+'.mhclo');V,UV,F,FUV=p.obj(mesh);m=p.proxy(mapping);Q,scale=p.fit(m,body);assert len(Q)==len(V);error=np.linalg.norm(p.to_blender(Q)-p.to_blender(V),axis=1);groups=p.components(len(V),F);row={'asset':stem,'obj':str(mesh),'proxy':str(mapping),'vertices':len(V),'faces':len(F),'uvVertices':len(UV),'referenceScales':scale.tolist(),'maximumReferenceOBJReconstructionErrorM':float(error.max()),'medianReferenceErrorM':float(np.median(error)),'maximumWeightNormalization':m['maximumWeightNormalization'],'header':m['header'],'mappingIndexBounds':[int(m['ids'].min()),int(m['ids'].max())],'components':[{'vertices':len(ids),'meanMH':V[ids].mean(0).tolist(),'boundsMH':[V[ids].min(0).tolist(),V[ids].max(0).tolist()]} for ids in groups],'licenseEmbeddedCC0': 'explicitly released as CC0' in mapping.read_text(encoding='utf8'),'dataSHA256':{'obj':hashlib.sha256(mesh.read_bytes()).hexdigest(),'proxy':hashlib.sha256(mapping.read_bytes()).hexdigest()}};rows.append(row)
    status='PASS_REFERENCE_PROXY_RECONSTRUCTION' if all(r['maximumReferenceOBJReconstructionErrorM']<.00005 and r['licenseEmbeddedCC0'] for r in rows) else 'FAIL_OR_REVIEW_REQUIRED';report={'status':status,'base':str(BASE),'baseSha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'baseVertices':len(body),'assets':rows,'format':'Barycentric/extrapolating native-vertex triples plus independently scaled XYZ offsets; own parser. Positive/negative weights normalized for affine translation invariance; no claim that all references form a convex triangle.'};(E/'reference-proxy-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
