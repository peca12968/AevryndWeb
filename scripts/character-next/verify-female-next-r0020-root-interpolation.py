"""Measure actual attachment root interpolation error, without moving geometry."""
import bpy,json,importlib.util,time
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('pin',Path(__file__).with_name('build-female-next-r0020-pinned-blink.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a=b.a
def main():
    report=json.loads((b.E/'a-build-verification.json').read_text());assert a.sha(b.DST)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(b.DST));rig=bpy.data.objects['AFN_R0005_Rig'];a.solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];P=np.array(a.solid.data(body)[0],np.float64);records=json.loads((b.R/'Evidence/character-female-next/r0010-eye-rim/c-spaced-lashes-lash-bindings.json').read_text())+json.loads((b.S/'aevrynd-female-next-r0018-c-brow-bindings.json').read_text());rest={name:np.array(a.solid.data(bpy.data.objects[name])[0],np.float64) for name in {r['object'] for r in records}};rows=[]
    for w in np.linspace(0,1,33):
        a.set_blink(float(w),float(w));Q=np.array(a.solid.data(body)[0],np.float64);actual={name:np.array(a.solid.data(bpy.data.objects[name])[0],np.float64) for name in rest};parts={}
        for rec in records:
            name=rec['object'];radial=6 if name.startswith('AFN10_') else 5;i=rec['firstVertex'];bc=np.array(rec['barycentric']);ids=np.array(rec['bodyVertices']);r0=rest[name][i:i+radial].mean(axis=0);r1=actual[name][i:i+radial].mean(axis=0);target=bc@Q[ids]+a.frame(Q[ids])@a.frame(P[ids]).T@(r0-bc@P[ids]);error=float(np.linalg.norm(r1-target));parts.setdefault(name,[]).append(error)
        rows.append({'weight':float(w),'objects':{name:{'roots':len(values),'maximumSkinFrameRootErrorM':max(values),'meanErrorM':float(np.mean(values))} for name,values in parts.items()}})
    maximum=max(o['maximumSkinFrameRootErrorM'] for row in rows for o in row['objects'].values());b.save('a-root-interpolation-verification.json',{'asset':str(b.DST),'assetSha256':a.sha(b.DST),'samples':rows,'maximumSkinFrameRootErrorM':maximum,'referenceToleranceM':.000001,'status':'PASS_SAMPLED_ROOT_ERROR' if maximum<=.000001 else 'FAIL_EXACT_INTERMEDIATE_BINDING','scope':'All 220 lash and 1080 brow root ring centres at 33 synchronized values, measured against actual evaluated skin-triangle frames and original root offsets. Sampling does not certify all time. No geometry changes or relaxed contact tolerances.'});print('R0020_ROOT_MAX_ERROR_M',maximum,flush=True)
if __name__=='__main__':main()
