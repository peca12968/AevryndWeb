"""Inspect saved animation timing and the actual diagnostic tube radius."""
import bpy,json,re,importlib.util
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
E=flow.R/'Evidence/character-female-next/r0015-guide-dynamics';proof=json.loads((E/'c-wind-blender-review.json').read_text());src=Path(proof['output']);assert flow.route.sha(src)==proof['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(src));d=np.load(flow.S/'aevrynd-female-next-r0015-c-wind-guides.npz');P=d['positions'];obj=bpy.data.objects['AFN15_CheckedGuideBank'];action=obj.data.shape_keys.animation_data.action;curves=[c for l in action.layers for s in l.strips for b in s.channelbags for c in b.fcurves]
for curve in curves:
    fi=int(re.search(r'Physics_(\d+)',curve.data_path).group(1));assert [p.co[0] for p in curve.keyframe_points]==[float(fi),float(fi+1),float(fi+2)] and all(p.interpolation=='LINEAR' for p in curve.keyframe_points)
rows=[]
for fi in (0,240,480,720):
    bpy.context.scene.frame_set(fi+1);bpy.context.view_layer.update();me=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;v=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',v);assert len(me.vertices)==48*64*6;rad=np.linalg.norm(v.reshape(48,64,6,3)-P[fi,:,:,None,:],axis=-1);maximum=float(rad.max());assert maximum<=.000061;rows.append({'sample':fi,'renderedTubeVertices':len(me.vertices),'maximumTubeVertexDistanceFromCentrelineM':maximum})
scene=bpy.context.scene;assert scene.render.fps==240 and scene.render.fps_base==1 and scene.frame_start==1 and scene.frame_end==721
(E/'c-wind-review-geometry-verification.json').write_text(json.dumps({'status':'PASS_SAVED_TIMING_AND_TUBE_ENVELOPE','assetSha256':proof['outputSha256'],'shapeKeyTimingCurvesChecked':len(curves),'allLinearTimingTriplesMatchPhysicsSamples':True,'tubeChecks':rows,'scope':'Display tube vertices remain inside the 60 um physics capsule plus the 1 um numerical allowance at listed samples. Polygon profile and linear sweep are diagnostic only, not child hair or self-collision acceptance.'},indent=2)+'\n');print('AFN15_REVIEW_GEOMETRY_PASS',flush=True)
