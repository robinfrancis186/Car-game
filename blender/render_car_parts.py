"""Actual Blender component inspection renders; these are not gameplay screenshots."""
import bpy,os
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'assets/car'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'roadster_studio.blend'))
s=bpy.context.scene;s.frame_set(1);s.cycles.samples=96;s.cycles.use_denoising=False;s.render.resolution_x=1000;s.render.resolution_y=900;s.render.resolution_percentage=100
studio=bpy.data.collections['STUDIO_ONLY'];studio_set=set(studio.all_objects);car=[o for o in bpy.data.objects if o.type=='MESH' and o not in studio_set]
cam=s.camera;cam.data.lens=60

def render(name,keep,location,target):
    for o in car:o.hide_render=not keep(o)
    cam.location=location;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/name);bpy.ops.render.render(write_still=True)

wheel_set=set(bpy.data.objects['Steer_Front_Right'].children_recursive)
render('part_wheel_and_steer_refined.png',lambda o:o in wheel_set,(2.35,-3.05,1.08),(1.35,-.924,.37))
render('part_rotor_and_caliper_refined.png',lambda o:o.name.startswith(('Brake_Rotor_Front_Right','Rotor_Drill_Front_Right','Brake_Caliper_Front_Right','Center_Hub_Front_Right','Lug_Front_Right')),(1.9,-2.5,.95),(1.35,-.924,.37))
cam.data.lens=50
prefixes=('Cockpit_Floor','Interior_','Seat_','Center_Console','Dashboard','Display_','Steering_')
render('part_right_hand_drive_cockpit_refined.png',lambda o:o.name.startswith(prefixes),(-1.6,-2.2,2.4),(-.05,0,.70))
cam.data.lens=60
render('part_bucket_seats_refined.png',lambda o:o.name.startswith(('Seat_','Cockpit_Floor')),(1.3,-2.0,1.75),(-.4,0,.7))
if os.environ.get('PARTS_ONLY')=='1':
    print('REFINED_PARTS_COMPLETE');raise SystemExit(0)
# Refreshed whole-car hero screenshots after the user reference revision.
for o in car:o.hide_render=False
s.render.resolution_x=1440;s.render.resolution_y=900;s.cycles.samples=192;cam.data.lens=52
render('hero_front.png',lambda o:True,(5.7,-6.6,2.65),(0,0,.62))
render('hero_rear.png',lambda o:True,(-5.4,5.9,2.6),(-.1,0,.6))
print('PART_RENDER_COMPLETE')
