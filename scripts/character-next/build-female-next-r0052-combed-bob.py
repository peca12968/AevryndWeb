"""Native Comb brush strokes on existing fibres; no sparse child interpolation."""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.view3d_utils import location_3d_to_region_2d
sp=importlib.util.spec_from_file_location('groom52',Path(__file__).with_name('inspect-female-next-r0052-native-groom.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;SRC=k.SRC
OUT=b.S/'aevrynd-female-next-r0052-a-native-combed-bob.blend'
NAME='AFN33_C_BODY_BOUND_FIBRES'
STROKES=[
    {'name':'left_middle_volume','view':(0,-1,0),'knots':[(-.073,-.090,1.451),(-.087,-.090,1.454),(-.099,-.090,1.442)],'radius':90,'strength':.55},
    {'name':'right_crown_sweep','view':(0,-1,0),'knots':[(.022,-.070,1.560),(.037,-.070,1.563),(.055,-.070,1.551)],'radius':82,'strength':.50},
    {'name':'right_lower_release','view':(0,-1,0),'knots':[(.078,-.067,1.397),(.094,-.067,1.402),(.103,-.067,1.391)],'radius':80,'strength':.55},
    {'name':'right_side_depth','view':(1,-.28,0),'knots':[(.083,.006,1.484),(.099,.006,1.491),(.108,.021,1.477)],'radius':80,'strength':.50},
    {'name':'left_tip_return','view':(-1,-.35,0),'knots':[(-.078,-.012,1.357),(-.070,-.019,1.351),(-.068,-.028,1.353)],'radius':72,'strength':.45},
]


if __name__ == "__main__":
    raise RuntimeError("Use run-female-next-r0052-native-events.py in a hidden native Blender session with --enable-event-simulate. Direct/background execution is unsupported; this module only supplies pinned inputs and artist stroke definitions.")
