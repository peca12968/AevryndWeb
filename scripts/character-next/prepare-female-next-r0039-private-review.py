"""Create a private viewport-only review copy; do not overwrite C1."""
import bpy,importlib.util,json
from pathlib import Path
import numpy as np
sp=importlib.util.spec_from_file_location('c39view',Path(__file__).with_name('build-female-next-r0039-complete-guides.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
PVT=a.E/'private';src=PVT/'aevrynd-female-next-r0039-c1-surface-transfer-study.blend';out=PVT/'aevrynd-female-next-r0039-c1-review.blend'
assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(src));obj=bpy.data.objects['AFN39_C1_PRIVATE_SURFACE_TRANSFER'];p,r=a.v.hair_arrays(obj)
for name in (a.f.OLD,a.m.GUIDE,a.m.REST):
    ob=bpy.data.objects.get(name)
    if ob:ob.hide_set(True)
obj.hide_set(False);bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.context.scene['AFN39_review']='Private Daniel Bystedt groom transfer;199representative segments unqualified. No adoption or score increase. Old owned scalp/helpers hidden only in viewport.'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(out));obj=bpy.data.objects['AFN39_C1_PRIVATE_SURFACE_TRANSFER'];q,s=a.v.hair_arrays(obj);assert np.array_equal(p,q) and np.array_equal(r,s)
assert bpy.data.objects[a.f.OLD].hide_get() and not obj.hide_get()
(PVT/'c1-review-viewport.json').write_text(json.dumps({'source':str(src),'sourceSha256':a.b.sha(src),'review':str(out),'reviewSha256':a.b.sha(out),'scope':'Only viewport visibility/selection/camera-view metadata changed; all displayed private strand positions/radii exact. All C1 contact/rights limitations remain. No source file overwritten.'},indent=2)+'\n')
print('C1_PRIVATE_REVIEW_READY',str(out),a.b.sha(out))
