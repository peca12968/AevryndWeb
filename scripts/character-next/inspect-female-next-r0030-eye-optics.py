"""Extract only existing CC0 eye geometry for fitted, contour-preserving optics."""
import bpy,importlib.util,json
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('b29',Path(__file__).with_name('build-female-next-r0029-native-eye-interface.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
E=q.b.R/'Evidence/character-female-next/r0030-eye-optics';E.mkdir(parents=True,exist_ok=True)
def main():
    assert q.b.sha(q.OUT)=='21c543b06ea5e92515294f48d3cb277ccaf1996b18e437dfa0fc1e86d4e8754f';bpy.ops.wm.open_mainfile(filepath=str(q.OUT));report={}
    fits=q.read('native-interface-inspection.json')['native']
    for side in ('L','R'):
        n='GEO-body_female_realistic.eye.'+side;o=bpy.data.objects[n];v,t=q.b.evaluated(o,True);center=np.array(fits[n]['fittedSphereCenterM']);radius=fits[n]['fittedMedianRadiusM'];cut=center[1]-np.sqrt(radius**2-.0054**2)
        report[side]={'name':n,'centerM':center.tolist(),'medianRadiusM':radius,'yRangeM':[float(v[:,1].min()),float(v[:,1].max())],'crossSectionPlaneYM':float(cut),'frontSagFromSectionM':float(cut-v[:,1].min()),'frontVertices':int((v[:,1]<cut).sum()),'sourceSignature':q.signature(o),'eyeMaterialProperties':{'thicknessMode':getattr(o.data.materials[0],'thickness_mode',None)} }
    (E/'existing-eye-inspection.json').write_text(json.dumps({'source':str(q.OUT),'sourceSha256':q.b.sha(q.OUT),'eyes':report,'scope':'Fixed original corneal/front-cap contour; iris dimensions are design inputs, not an individual biometric calibration.'},indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
