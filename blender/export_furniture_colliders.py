"""V8 oriented-box/capsule proxies for fixed course furniture.
Continuous elevated-road edges/underside use elevated_corridors, not duplicate beads.
"""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/course/Kappil_Coast.blend'))
bpy.context.view_layer.update();out=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or not o.name.startswith(('Gate_Pillar','Gate_Crossbar','Bridge_Rail','Bridge_Post')):continue
 corners=[Vector(v) for v in o.bound_box];lo=Vector(tuple(min(v[i] for v in corners) for i in range(3)));hi=Vector(tuple(max(v[i] for v in corners) for i in range(3)));center=(lo+hi)/2;dims=hi-lo;world=o.matrix_world@center;wc=[o.matrix_world@v for v in corners];bottom=min(v.z for v in wc);top=max(v.z for v in wc)
 if o.name.startswith('Bridge_Rail'):
  axis=0 if dims.x>=dims.y else 1;rad=max(.06,dims[1-axis]/2);a=center.copy();b=center.copy();a[axis]=lo[axis]+rad;b[axis]=hi[axis]-rad;a=o.matrix_world@a;b=o.matrix_world@b
  out.append({'id':'furniture-'+o.name,'shape':'capsule','x':a.x,'z':-a.y,'endX':b.x,'endZ':-b.y,'radius':rad,'y':bottom,'height':top-bottom,'kind':'bridge_rail'})
 else:
  heading=-o.rotation_euler.z
  out.append({'id':'furniture-'+o.name,'shape':'box','x':world.x,'z':-world.y,'radius':math.hypot(dims.x/2,dims.y/2),'halfLength':dims.x/2,'halfWidth':dims.y/2,'heading':heading,'y':bottom,'height':top-bottom,'kind':'checkpoint_structure' if o.name.startswith('Gate') else 'bridge_post'})
report={'basis':'Three +X east,+Y up,+Z south; metres; heading atan2(+Z,+X)','type':'v8 OBB/capsule proxies from authored furniture. Flyover barriers/underside use continuous elevated_corridors.','source':'assets/course/Kappil_Coast.blend','colliders':out}
for folder in ['assets/web','web/public/assets']:(ROOT/folder/'furniture_colliders.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
print('V8_FURNITURE_COLLIDERS',len(out),'CAPSULES',sum(c['shape']=='capsule' for c in out))
