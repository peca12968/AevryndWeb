import bpy
for n in ['HairCoverageTiles_v246','HairSilhouetteCards_v246','HairDetailFibers_v246','HairlineNaturalCards_v214']:
 o=bpy.data.objects.get(n)
 if o: print(n,[m.name for m in o.data.materials])
for m in bpy.data.materials:
 if 'Hair' in m.name or 'hair' in m.name: print('MAT',m.name,m.surface_render_method if hasattr(m,'surface_render_method') else '',m.diffuse_color[:])
