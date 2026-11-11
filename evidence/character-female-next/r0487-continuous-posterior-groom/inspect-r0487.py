from pathlib import Path
import json
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'r0486-primary-guide-foundation/female-next-r0486-primary-guides-UNACCEPTED.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False, use_scripts=False)
body = bpy.data.objects['R482 archived complete neutral skin']
hair = bpy.data.objects['R486 complete hair | primary guide foundation']
vertices = np.empty((len(body.data.vertices), 3), dtype='f4')
body.data.vertices.foreach_get('co', vertices.ravel())
positions = np.empty((24831, 80, 3), dtype='f4')
hair.data.position_data.foreach_get('vector', positions.ravel())
roots = positions[:, 0]
ear_rows = {}
for side in (-1, 1):
    rows = []
    for z in np.arange(1.43, 1.56, .008):
        slab = vertices[(abs(vertices[:, 2] - z) < .004) & (vertices[:, 1] > -.065) & (vertices[:, 1] < .055)]
        if len(slab):
            rows.append([round(z, 4), *np.round(slab[np.argmax(slab[:, 0] * side)], 5).tolist()])
    ear_rows[str(side)] = rows
record = dict(bodyMatrix=list(map(list,body.matrix_world)), hairMatrix=list(map(list,hair.matrix_world)),
    rootBounds=np.quantile(roots, [0,.1,.5,.9,1], axis=0).tolist(),
    tipBounds=np.quantile(positions[:,-1], [0,.1,.5,.9,1], axis=0).tolist(),
    earLateralByHeight=ear_rows,
    bodyMesh=body.data.name, vertices=len(vertices), polygons=len(body.data.polygons),
    rootCoordinateFrame='aligned neutral scalp and child object local metres')
(ROOT / 'inspection.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record), flush=True)
