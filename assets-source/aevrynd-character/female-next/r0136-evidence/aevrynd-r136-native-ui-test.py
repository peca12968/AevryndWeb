import bpy,runpy,traceback
def run():
 try:runpy.run_path('C:/Users/USER/AppData/Local/Temp/aevrynd-r136-native-comb-test.py',run_name='__main__')
 except:traceback.print_exc()
 finally:bpy.ops.wm.quit_blender()
bpy.app.timers.register(run,first_interval=.5)
