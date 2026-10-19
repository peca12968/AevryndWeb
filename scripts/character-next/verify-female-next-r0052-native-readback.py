"""Independent saved native/evaluated data and effective brush setting audit."""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,sys
sp=importlib.util.spec_from_file_location('g52read',Path(__file__).with_name('inspect-female-next-r0052-native-groom.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E

def scalar_props(data):
    if data is None:return None
    return {p.identifier:getattr(data,p.identifier) for p in data.bl_rna.properties
            if p.type in ('BOOLEAN','INT','FLOAT','ENUM','STRING') and not getattr(p,'is_array',False)}

def main():
    tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(k.SRC));before=f.state()
    old=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];name=old.name;P,R=f.v.hair_arrays(old)
    oldTypes=np.array([r.value for r in old.data.attributes['curve_type'].data])
    sourceUnified=scalar_props(bpy.context.scene.tool_settings.curves_sculpt.unified_paint_settings) if bpy.context.scene.tool_settings.curves_sculpt else None
    rows=[]
    tags=('b-fixed',) if '--fixed-only' in sys.argv else ('a','b')
    for tag in tags:
        summary=json.loads((E/(tag+'-build-summary.json')).read_text());path=Path(summary['output']);assert b.sha(path)==summary['outputSha256']
        bpy.ops.wm.open_mainfile(filepath=str(path));after=f.state();o=bpy.data.objects[name]
        assert all(before[key]==after[key] for key in ('meshes','materials','skinFields','stage'))
        assert all(after['curves'][name]==value for name,value in before['curves'].items() if name!=o.name)
        Q,RR=f.v.hair_arrays(o);EP,ER=f.v.hair_arrays(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        assert Q.shape==P.shape and np.array_equal(R,RR)
        assert np.array_equal(oldTypes,np.array([r.value for r in o.data.attributes['curve_type'].data]))
        assert np.array_equal(P[:,0],Q[:,0])
        row={'tag':tag,'source':str(path),'sourceSha256':b.sha(path),'reopened':True,
            'bodyAllOtherMeshesMaterialsFieldsAndStageExact':True,'browCurvesExact':True,
            'nativeRootsRadiiPointCountsCurveTypesExact':True,'curves':len(P),'pointsPerCurve':P.shape[1],
            'changedCurves':int(np.any(np.linalg.norm(Q-P,axis=2)>1e-8,axis=1).sum()),
            'maximumLocalDisplacementM':float(np.linalg.norm(Q-P,axis=2).max()),
            'nativeVsEvaluatedMaximumM':float(np.linalg.norm(Q-EP,axis=2).max()),
            'nativeVsEvaluatedRadiiExact':bool(np.array_equal(RR,ER)),
            'sourceUnifiedPaintSettings':sourceUnified,
            'savedUnifiedPaintSettings':scalar_props(bpy.context.scene.tool_settings.curves_sculpt.unified_paint_settings),
            'savedBrush':bpy.context.scene.tool_settings.curves_sculpt.brush.name if bpy.context.scene.tool_settings.curves_sculpt.brush else None,
            'libraries':[{'name':lib.name,'path':lib.filepath} for lib in bpy.data.libraries],
            'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],
            'contactLimit':'Pilot contacts only so far; saved geometry readback does not certify full candidate body/self/other-mesh contacts or dynamics.'}
        rows.append(row);k.save(('b-fixed-saved-native-readback.json' if '--fixed-only' in sys.argv else 'saved-native-readback.json'),{'status':'PASS_SAVED_NATIVE_INVARIANTS_NO_CHARACTER_ACCEPTANCE','rows':rows,'seconds':time.time()-tick})
        print('R52_REOPEN',tag,row['changedCurves'],row['nativeVsEvaluatedMaximumM'],row['savedUnifiedPaintSettings'],flush=True)

if __name__=='__main__':main()
