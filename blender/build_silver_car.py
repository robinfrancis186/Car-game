"""Original silver wedge fan concept: Blender-authored, articulated browser asset.
User supplied photos were visual references only. No photographs/CAD are embedded.
Fictional thruster sockets are game VFX attachment points, not an engineering model.
"""
import bpy, bmesh, math, json, shutil, struct, sys, hashlib
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/web'; OUT.mkdir(exist_ok=True, parents=True)
DETAIL=ROOT/'assets/cars/silver_refinement'; DETAIL.mkdir(exist_ok=True,parents=True)
sys.path.insert(0,str(ROOT/'blender'))
from rebuild_car_helpers import smooth_interp
# Reuse the exact already validated Silver wheel geometry, not an earlier red-wheel derivative.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(DETAIL/'baseline/car_silver.glb'))
scene=bpy.context.scene
root=bpy.data.objects['CAR_ROOT']
# Preserve only the original generated wheel assemblies and the documented rig.
keep={root}
for o in bpy.data.objects:
    if o.name.startswith(('Steer_','Spin_','Wheel_','Caliper_')): keep.add(o)
for o in list(bpy.data.objects):
    if o not in keep: bpy.data.objects.remove(o,do_unlink=True)
root['prototype']='Original angular silver fan concept; not manufacturer CAD. Flight handling and VFX are fictional gameplay.'
root['source']='Original Blender geometry. User-supplied images used only as visual references.'
parts=[]
def mat(name,c,metal=.0,rough=.3,emit=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF'); n.inputs['Base Color'].default_value=(*c[:3],1)
    n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough
    n.inputs['Transmission Weight'].default_value=0
    n.inputs['Coat Weight'].default_value=.30 if metal>.5 else .12
    n.inputs['Coat Roughness'].default_value=.18
    if emit:n.inputs['Emission Color'].default_value=(*c[:3],1);n.inputs['Emission Strength'].default_value=emit
    m.diffuse_color=(*c[:3],1)
    return m
paint=mat('Crimson multi-coat | original fan concept',(.32,.35,.37),.78,.30)
black=mat('Silver concept | satin carbon aero',(.012,.016,.019),.28,.28)
glass=mat('Silver concept | neutral smoked glazing',(.018,.032,.041),.12,.085)
gp=glass.node_tree.nodes.get('Principled BSDF');gp.inputs['Alpha'].default_value=.72;gp.inputs['Coat Weight'].default_value=.65;gp.inputs['Coat Roughness'].default_value=.07;gp.inputs['IOR'].default_value=1.46
glass.diffuse_color=(.018,.032,.041,.72);glass.surface_render_method='DITHERED';glass.use_transparency_overlap=False
interior=mat('Silver concept | charcoal sport upholstery',(.018,.022,.024),.02,.57)
trim=mat('Silver concept | shadow panel gaps',(.004,.005,.007),.10,.34)
alloy=mat('Silver concept | machined nozzle titanium',(.30,.22,.105),.85,.25)
white=mat('Silver concept | laser white running light',(.68,.89,1),.25,.18,3)
red=mat('Silver concept | rear red ribbon',(.70,.006,.008),.15,.17,2.7)
plate=mat('Silver concept | ceramic rear plate',(.60,.66,.68),.25,.35)

def mesh(name,v,f,material,bevel=0,smooth=False,parent=None,collect=True):
    d=bpy.data.meshes.new(name+'_Geometry');d.from_pydata(v,[],f);d.update()
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);d.materials.append(material)
    bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free()
    for p in d.polygons:p.use_smooth=smooth
    if bevel:
        mod=o.modifiers.new('Manufactured edge radii','BEVEL');mod.width=bevel;mod.segments=3;mod.limit_method='ANGLE';mod.angle_limit=.35
        mod.harden_normals=True
        norm=o.modifiers.new('Panel weighted normals','WEIGHTED_NORMAL');norm.keep_sharp=True
    if parent:
        bpy.context.view_layer.update();mw=o.matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted();o.matrix_basis=mw
    if collect:parts.append(o)
    return o

def cube(name,loc,size,material,bevel=.01,rot=None,parent=None,collect=True):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rot:o.rotation_euler=rot
    o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
        mod.harden_normals=True;norm=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');norm.keep_sharp=True
    if parent:
        bpy.context.view_layer.update();mw=o.matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted();o.matrix_basis=mw
    if collect:parts.append(o)
    return o

def cylinder(name,loc,radius,depth,material,axis='Z',vertices=32,collect=True):
    rot=(0,math.pi/2,0) if axis=='X' else ((math.pi/2,0,0) if axis=='Y' else (0,0,0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object;o.name=name;o.data.materials.append(material)
    b=o.modifiers.new('Machined edge radius','BEVEL');b.width=.002;b.segments=2
    for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.5
    if collect:parts.append(o)
    return o

def torus(name,loc,major,minor,material,axis='X'):
    rot=(0,math.pi/2,0) if axis=='X' else (0,0,0)
    bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=8,location=loc,rotation=rot,major_radius=major,minor_radius=minor)
    o=bpy.context.object;o.name=name;o.data.materials.append(material)
    for p in o.data.polygons:p.use_smooth=True
    parts.append(o);return o

def line(name,pts,radius,material):
    curve=bpy.data.curves.new(name+'_Curve','CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=radius;curve.bevel_resolution=2
    s=curve.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,curve);scene.collection.objects.link(o);o.data.materials.append(material);parts.append(o);return o

def empty(name,loc,parent=root):
    o=bpy.data.objects.new(name,None);scene.collection.objects.link(o);o.parent=parent;o.location=loc;o.empty_display_size=.08;return o
# Closed multi-faceted body, with substantial fender shoulders and genuine arch openings.
stations=[(-2.23,.955,.845,.885),(-1.82,1.045,.860,.940),(-1.35,1.067,.850,.940),(-.90,1.020,.835,.925),(-.15,.982,.820,.905),(.82,1.015,.820,.900),(1.35,1.067,.785,.858),(1.68,1.055,.730,.777),(2.05,.985,.640,.663),(2.29,.835,.575,.575)]
def props(x):
    return smooth_interp(stations,x)
def top(x,y):
    w,zc,zs=props(x);q=min(1,abs(y)/w)
    return smooth_interp([(0,zc),(.44,zc+.027),(.76,zc+.040),(.92,zs+.010),(.975,zs-.026),(1,zs-.085)],q)[0]
def sweep_x(x,y):
    return x-.075*max(0,(x-1.68)/.61)**2*(abs(y)/props(x)[0])**2
# Closely sampled, smoothly shaded pressed-metal shoulders retain the angular
# concept's wedge proportion while removing the previous ten-station facets.
v=[];xs=[stations[0][0]+(stations[-1][0]-stations[0][0])*i/90 for i in range(91)]
for x in xs:
    w,zc,zs=props(x)
    half=[(w*q,top(x,w*q)) for q in (0,.22,.44,.62,.76,.86,.92,.96,.985,1)]
    upper=zs-.085
    half +=[(w*.999,upper*.76+.355*.24),(w*.990,upper*.44+.355*.56),(w*.974,upper*.18+.355*.82),(w*.968,.355),(w*.90,.274),(w*.82,.245),(0,.235)]
    ring=half+[(-y,z) for y,z in reversed(half[1:-1])]
    v.extend((sweep_x(x,y),y,z) for y,z in ring)
f=[];N=len(ring)
for i in range(len(xs)-1):
    for j in range(N):f.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
f.extend([tuple(reversed(range(N))),tuple((len(xs)-1)*N+j for j in range(N))])
body=mesh('Wedge_Body_Shell',v,f,paint,smooth=True)
# Triangulation before successive wheel/cabin booleans avoids ambiguous long ngons.
tr=body.modifiers.new('Deterministic metal tessellation','TRIANGULATE');bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=tr.name)
for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
    hub=bpy.data.objects['Steer_'+key].location.copy()
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.403,depth=.72,location=(hub.x,math.copysign(1.0,hub.y),hub.z),rotation=(math.pi/2,0,0));cut=bpy.context.object
    mod=body.modifiers.new('True wheel aperture '+key,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
    bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# A real recessed cockpit well supports the readable, translucent glazing.
outline=[(.54,-.64),(.54,.64),(-1.16,.64),(-1.16,-.64)]
cv=[(x,y,z) for z in (.385,1.50) for x,y in outline]
cf=[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
cut=mesh('Cockpit_Well_Cutter',cv,cf,black,collect=False)
mod=body.modifiers.new('Actual cockpit well','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
# Deliberately no hardened weighted normals on the flowing main shell.
# True black arch lips hide the inner silver rim and give the wheels a recessed fit.
for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']:
    hub=bpy.data.objects['Steer_'+key].location;side=1 if hub.y>0 else -1
    pts=[]
    for i in range(49):
        a=math.pi*i/48;x=hub.x+.406*math.cos(a);z=hub.z+.406*math.sin(a);w=props(x)[0]
        pts.append((x,side*(w+.002),z))
    # Small-radius trim deliberately remains inside the fender silhouette.
    line('Wheel_Arch_Trim_'+key,pts,.004,black)
# Lower aero structures and a deep black front fascia.
tray=[(2.16,.77),(1.84,.79),(1.81,.62),(.91,.62),(.87,.86),(-.87,.86),(-.91,.62),(-1.81,.62),(-1.87,.79),(-2.18,.78)]
tray=tray+[(x,-y) for x,y in reversed(tray)]
nt=len(tray);tv=[(x,y,z) for z in [.215,.260] for x,y in tray]
tf=[tuple(reversed(range(nt))),tuple(nt+i for i in range(nt))]+[(i,(i+1)%nt,(i+1)%nt+nt,i+nt) for i in range(nt)]
mesh('Carbon_Battery_Undertray',tv,tf,black,.007)
for side in [-1,1]:
    mesh('Carbon_Rocker_'+str(side),[(-.91,side*.99,.28),(.92,side*1.025,.28),(.90,side*1.06,.245),(-1.02,side*1.05,.245),(-.91,side*.99,.32),(.92,side*1.025,.32)],[(0,1,2,3),(0,4,5,1),(1,5,2),(0,3,4)],black,.008)
def nose_x(y):return 2.301-.075*(abs(y)/.835)**2
fv=[]
for z in [.365,.524]:
    for i in range(49):
        y=-.805+1.61*i/48;fv.append((nose_x(y)+.004,y,z+.008*(y/.805)**2))
mesh('Swept_Front_Shadow_Fascia',fv,[(i,i+1,50+i,49+i) for i in range(48)],black,smooth=True)
line('Front_Continuous_Laser_LED',[(nose_x(y)+.009,y,.548+.006*(y/.81)**2) for y in [-.81+1.62*i/64 for i in range(65)]],.0055,white)
# Narrow lower sculpted blade instead of a solid rectangular front bumper.
line('Front_Lower_Aero_Blade',[(nose_x(y)+.005,y,.342+.008*(y/.81)**2) for y in [-.81+1.62*i/48 for i in range(49)]],.011,black)
mesh('Front_Carbon_Splitter',[(2.34,-.89,.255),(2.34,.89,.255),(2.12,1.005,.265),(1.94,.99,.265),(1.94,-.99,.265),(2.12,-1.005,.265),(2.34,-.89,.238),(2.34,.89,.238),(2.12,1.005,.248),(1.94,.99,.248),(1.94,-.99,.248),(2.12,-1.005,.248)],[(0,1,2,3,4,5),(6,11,10,9,8,7)]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)],black,.006)
# Two slim cooling slits in the black front fascia: tiny titanium edges, dark interior.
for side in [-1,1]:
    cube('Front_Lower_Cooling_Opening_'+str(side),(nose_x(side*.43)+.008,side*.43,.395),(.009,.29,.020),trim,.009)
# Hood fold lines are subtle black shut-lines, following the silver surface.
for side in [-1,1]:
    pts=[]
    for i in range(21):
        t=i/20;x=.80+1.26*t;y=side*(.57+.09*t);pts.append((sweep_x(x,y),y,top(x,y)+.006))
    line('Hood_Panel_Shutline_'+str(side),pts,.0017,trim)
# Shared exact glass boundaries avoid the floating-canopy defects of independent slabs.
def windpoint(t,u):
    x=.82*(1-t)-.12*t;w=.74*(1-t)+.635*t
    low=top(.82,.74*u)+.008;hi=1.225-.035*u*u
    return (x-.045*math.sin(math.pi*t)*(1-u*u),u*w,low*(1-t)+hi*t+.045*math.sin(math.pi*t)*(1-.25*u*u))
def roofpoint(t,u):
    return (-.12-.63*t,u*(.635+.020*t),(1.225-.020*t)-.035*u*u+.021*math.sin(math.pi*t))
def rearpoint(t,u):
    low=top(-1.31,.81*u)+.008
    return (-.75-.56*t,u*(.655+.155*t),(1.205-.035*u*u)*(1-t)+low*t+.012*math.sin(math.pi*t))
def patch(name,func,nt=16,nu=24):
    verts=[func(i/nt,2*j/nu-1) for i in range(nt+1) for j in range(nu+1)]
    faces=[(i*(nu+1)+j,i*(nu+1)+j+1,(i+1)*(nu+1)+j+1,(i+1)*(nu+1)+j) for i in range(nt) for j in range(nu)]
    return mesh(name,verts,faces,glass,smooth=True)
patch('Continuous_Front_Glass',windpoint)
patch('Continuous_Roof_Glass',roofpoint,10,24)
patch('Continuous_Rear_Glass',rearpoint,10,24)
for side in [-1,1]:
    def sidepoint(t,u,side=side):
        q=(u+1)/2
        xb=.82-2.13*t;yb=.74+.07*t;zb=top(xb,yb)+.008
        xt=-.12-.63*t;yt=.635+.020*t;zt=1.19-.020*t+.021*math.sin(math.pi*t)
        return (xb*(1-q)+xt*q,side*(yb*(1-q)+yt*q+.027*math.sin(math.pi*q)),zb*(1-q)+zt*q)
    patch('Flush_Side_Glass_'+str(side),sidepoint,20,10)
    # Slender bonded front pillar, shared with the actual windshield border.
    line('Silver_A_Pillar_'+str(side),[windpoint(i/20,side) for i in range(21)],.0105,paint)
    line('Roof_Edge_'+str(side),[roofpoint(i/18,side) for i in range(19)],.010,paint)
    line('Side_Lower_Seal_'+str(side),[sidepoint(i/32,-1) for i in range(33)],.005,trim)
    a=roofpoint(1,side);b=rearpoint(1,side);c=(-1.62,side*.995,top(-1.62,.995)+.006)
    mesh('Sculpted_Silver_C_Pillar_'+str(side),[a,b,c,(-1.39,side*1.023,top(-1.39,1.023)+.006)],[(0,1,2,3)],paint,.006)
    # Tapered side mirrors, silver caps and deep black mirrored face.
    line('Mirror_Stalk_'+str(side),[(.53,side*.79,.895),(.48,side*.99,.91)],.014,black)
    cube('Wing_Mirror_Shell_'+str(side),(.48,side*1.055,.924),(.255,.145,.075),paint,.029,rot=(0,.03,-side*.08))
    cube('Wing_Mirror_Glass_'+str(side),(.351,side*1.055,.924),(.008,.111,.046),glass,.011)
    # Faceted door seams and a flush handle. Surface y follows tapered body width.
    seam=[]
    for x,z in [(.70,.866),(.66,.70),(.59,.36),(.46,.31),(-.78,.31),(-.91,.39),(-.96,.70),(-1.0,.89)]:
        w,zc,zs=props(x);seam.append((x,side*(w+.004),z))
    line('Door_Panel_Gap_'+str(side),seam,.0022,trim)
    cube('Flush_Door_Handle_'+str(side),(-.71,side*1.020,.767),(.142,.012,.018),black,.005)
    cube('Fender_Air_Blade_'+str(side),(.82,side*1.020,.695),(.042,.014,.185),black,.012,rot=(0,.13,0))
# Compact original cockpit: visible below the neutral glazing, not a cockpit mode claim.
cube('Cockpit_Recessed_Floor',(-.29,0,.40),(1.70,1.26,.04),black,.015)
cube('Cockpit_Backwall',(-1.13,0,.60),(.035,1.25,.40),interior,.012)
cube('Low_Wrapped_Dashboard',(.40,0,.765),(.32,1.24,.125),interior,.05)
cube('Central_Sculpted_Tunnel',(-.19,0,.49),(1.20,.16,.15),black,.035)
for side in [-1,1]:
    yy=side*.34
    cube('Sport_Seat_Base_'+str(side),(-.40,yy,.48),(.49,.38,.12),interior,.055)
    cube('Sport_Seat_Back_'+str(side),(-.73,yy,.72),(.115,.38,.48),interior,.055,rot=(0,-.15,0))
    cube('Integrated_Headrest_'+str(side),(-.78,yy,.982),(.10,.26,.15),interior,.045)
    for sg in [-1,1]:
        line('Seat_Contoured_Bolster_'+str(side)+'_'+str(sg),[(-.17,yy+sg*.17,.52),(-.46,yy+sg*.19,.55),(-.68,yy+sg*.19,.75),(-.73,yy+sg*.14,.92)],.027,interior)
        line('Seat_Stitch_Seam_'+str(side)+'_'+str(sg),[(-.18,yy+sg*.16,.545),(-.45,yy+sg*.17,.575),(-.66,yy+sg*.17,.77),(-.72,yy+sg*.13,.93)],.002,plate)
# Original unbranded steering and low instrument binnacle.
cube('Driver_Instrument_Binnacle',(.22,-.34,.83),(.15,.31,.10),black,.025)
cube('Dark_Instrument_Face',(.139,-.34,.833),(.009,.25,.06),glass,.01)
torus('Sport_Steering_Rim',(.02,-.34,.87),.115,.012,black,'X')
for angle in [math.pi/2,7*math.pi/6,11*math.pi/6]:
    line('Steering_Spoke_'+str(angle),[(.015,-.34,.87),(.015,-.34+.105*math.cos(angle),.87+.105*math.sin(angle))],.008,alloy)
cylinder('Unbranded_Steering_Hub',(.014,-.34,.87),.032,.025,black,'X',24)
# Rear band and recessed four-nozzle fiction package.
cube('Rear_Shadow_Fascia',(-2.239,0,.530),(.025,1.840,.505),black,.018)
cube('Rear_Lightbar_Socket',(-2.243,0,.838),(.022,1.84,.041),black,.010)
cube('Rear_Continuous_Red_LED',(-2.261,0,.845),(.013,1.817,.015),red,.005)
cube('Rear_Ceramic_Plate',(-2.259,0,.728),(.016,.30,.083),plate,.007)
for i,y in enumerate([-.63,-.21,.21,.63]):
    cylinder('FICTIONAL_Rear_Nozzle_Housing_'+str(i),(-2.252,y,.555),.075,.027,black,'X')
    torus('FICTIONAL_Rear_Nozzle_Ring_'+str(i),(-2.270,y,.555),.062,.006,alloy)
    cylinder('FICTIONAL_Rear_Nozzle_Dark_Core_'+str(i),(-2.268,y,.555),.053,.006,trim,'X')
    torus('FICTIONAL_Rear_Nozzle_Inner_Ring_'+str(i),(-2.273,y,.555),.043,.0025,alloy)
    empty('Thruster_Rear_'+str(i),(-2.29,y,.555))
for side,tag in [(-1,'RR'),(1,'RL')]:
    cylinder('FICTIONAL_Down_Nozzle_Casing_'+tag,(-1.98,side*.82,.281),.074,.15,black,'Z')
    torus('FICTIONAL_Down_Nozzle_Ring_'+tag,(-1.98,side*.82,.203),.058,.006,alloy,'Z')
    cylinder('FICTIONAL_Down_Nozzle_Core_'+tag,(-1.98,side*.82,.205),.049,.008,trim,'Z')
    empty('Thruster_Down_'+tag,(-1.98,side*.82,.19))
# Rear diffuser fins reinforce depth without creating excessive browser primitives.
for y in [-.71,-.43,0,.43,.71]:
    mesh('Rear_Diffuser_Fin_'+str(y),[(-2.28,y,.30),(-1.87,y,.26),(-1.89,y,.405),(-2.28,y,.38),(-2.28,y+.012,.30),(-1.87,y+.012,.26),(-1.89,y+.012,.405),(-2.28,y+.012,.38)],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],black,.003)
# The rear wing is a separate articulated Blender assembly, not baked into CarBody.
hinge=empty('AeroWing_Hinge',(-1.99,0,1.08));hinge['axis']='Blender local Y; Three local -Z';hinge['role']='Fictional active aero; game should animate this pivot, not CarBody.'
for side in [-1,1]:
    mesh('Wing_Static_Pylon_'+str(side),[(-2.04,side*.61,.88),(-1.87,side*.61,.88),(-1.90,side*.61,1.18),(-2.01,side*.61,1.18),(-2.04,side*.635,.88),(-1.87,side*.635,.88),(-1.90,side*.635,1.18),(-2.01,side*.635,1.18)],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],black,.008)
wingparts=[]
# A swept airfoil with a crisp trailing edge and a gently convex upper face.
profile=[(-1.735,1.230),(-1.765,1.263),(-1.93,1.276),(-2.235,1.252),(-2.235,1.234),(-1.94,1.237),(-1.77,1.212)]
wv=[(x,y,z) for y in [-1.005,1.005] for x,z in profile];wn=len(profile)
wf=[tuple(reversed(range(wn))),tuple(wn+i for i in range(wn))]+[(i,(i+1)%wn,(i+1)%wn+wn,i+wn) for i in range(wn)]
wingparts.append(mesh('Active_Aero_Mainplane',wv,wf,black,.006,parent=hinge,collect=False))
for side in [-1,1]:
    wingparts.append(mesh('Active_Aero_Endplate_'+str(side),[(-1.72,side*1.012,1.222),(-1.79,side*1.012,1.328),(-2.24,side*1.012,1.343),(-2.25,side*1.012,1.206),(-1.72,side*1.028,1.222),(-1.79,side*1.028,1.328),(-2.24,side*1.028,1.343),(-2.25,side*1.028,1.206)],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],black,.005,parent=hinge,collect=False))
# Bake modifiers and curves, then merge static pieces to one paint-recolorable mesh.
def merge(objects,name,parent):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.convert(target='MESH')
    # Keep glazing grids and main silhouette; trim subpixel bevel/nozzle/curve tessellation.
    audit=[]
    for item in objects:
        item.data.calc_loop_triangles();n=len(item.data.loop_triangles)
        target=n if ('Glass' in item.name or item.name=='Wedge_Body_Shell' or item.name.startswith('Active_Aero')) else 210
        if n>target:
            bpy.context.view_layer.objects.active=item
            dec=item.modifiers.new('Browser microdetail LOD','DECIMATE');dec.ratio=target/n;dec.use_collapse_triangulate=True
            bpy.ops.object.modifier_apply(modifier=dec.name)
        item.data.calc_loop_triangles();audit.append((item.name,n,len(item.data.loop_triangles)))
    print('SILVER_PART_LOD',name,json.dumps(audit))
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join();o=bpy.context.object;o.name=name
    bpy.context.view_layer.update();mw=o.matrix_world.copy();o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted();o.matrix_basis=mw
    # Apply transforms without disturbing the explicit hierarchy origins.
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o
# Editable pre-merge native source retains individually named authored panels.
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(DETAIL/'silver_editable.blend'),compress=True)
body=merge(parts,'CarBody',root);wing=merge(wingparts,'AeroWing',hinge)
# Name and dimensions are metadata, not manufacturer specifications.
root['design']='Angular silver concept inspired by user images; original approximate fan mesh.'
for o in [body,wing]:o['original_geometry']=True
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'car_silver.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'car_silver.glb'),export_format='GLB',use_selection=True,export_animations=False,export_apply=True,export_yup=True,export_extras=True)
sys.path.insert(0,str(DETAIL))
from clean_silver_glb import clean
cleanup=clean(OUT/'car_silver.glb');(DETAIL/'degenerate_cleanup.json').write_text(json.dumps(cleanup,indent=2))
blob=(OUT/'car_silver.glb').read_bytes();n=struct.unpack_from('<I',blob,12)[0];g=json.loads(blob[20:20+n])
tri=sum(g['accessors'][p['indices']]['count']//3 for me in g['meshes'] for p in me['primitives']);draws=sum(len(me['primitives']) for me in g['meshes'])
steers={key:bpy.data.objects['Steer_'+key] for key in ['Front_Left','Front_Right','Rear_Left','Rear_Right']}
manifest={'result':'PASS' if tri<=42000 and draws<=40 else 'REVIEW','file':'car_silver.glb','bytes':len(blob),'triangles':tri,'material_draw_calls':draws,'mesh_nodes':len(g['meshes']),'sha256':hashlib.sha256(blob).hexdigest(),'revision':'V13 bounded Silver surface/glazing refinement','editable_source':'assets/cars/silver_refinement/silver_editable.blend','glazing_material':glass.name,'glazing_runtime_note':'Name intentionally uses glazing, not glass, to preserve authored neutral tint rather than legacy runtime bronze override.','max_visual_steer_rad':.4,'car_root':'CAR_ROOT','body_mesh':'CarBody','paint_material':'Crimson multi-coat | original fan concept','forward':'+X','up':'+Y','left':'-Z','steer_axis':'Three local +Y','spin_axis_for_forward':'Three local -Z','wheel_radius_m':.366,'steer_nodes':['Steer_'+k for k in steers],'spin_nodes':['Spin_'+k for k in steers],'wheel_centers_three':{k:[o.location.x,o.location.z,-o.location.y] for k,o in steers.items()},'aero_hinge':'AeroWing_Hinge','aero_axis':'Three local -Z','thruster_sockets':['Thruster_Rear_'+str(i) for i in range(4)]+['Thruster_Down_RL','Thruster_Down_RR'],'rights':'No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. Original project geometry; no photograph textures, downloaded CAD or manufacturer logos.','limitations':['Approximate fan concept based on user-supplied visual references; not an accurate manufacturer model.','Neutral smoked alpha glazing with a compact original cockpit; not a separately validated interior-camera experience.','Flight, active aero behavior and nozzle arrangement are fictional game mechanics, not production claims.','Materials use compact PBR values rather than photographic textures.']}
(OUT/'car_silver_manifest.json').write_text(json.dumps(manifest,indent=2))
public=ROOT/'web/public/assets';public.mkdir(parents=True,exist_ok=True);shutil.copyfile(OUT/'car_silver.glb',public/'car_silver.glb')
# Reimport the actual GLB rather than rendering the construction scene.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(OUT/'car_silver.glb'))
bpy.context.view_layer.update()
checks=[]
for key in steers:
    s=bpy.data.objects.get('Steer_'+key);sp=bpy.data.objects.get('Spin_'+key);wheel=bpy.data.objects.get('Wheel_'+key);cal=bpy.data.objects.get('Caliper_'+key)
    checks.append({'wheel':key,'steer_present':bool(s),'spin_parent_correct':bool(sp and sp.parent==s),'wheel_spins':bool(wheel and wheel.parent==sp),'caliper_does_not_spin':bool(cal and cal.parent==s),'hub_blender':list(s.matrix_world.translation) if s else None})
allv=[o.matrix_world@v.co for o in bpy.data.objects if o.type=='MESH' for v in o.data.vertices]
mins=[min(v[i] for v in allv) for i in range(3)];maxs=[max(v[i] for v in allv) for i in range(3)]
validation={'result':'PASS' if all(all(c[k] for k in ['steer_present','spin_parent_correct','wheel_spins','caliper_does_not_spin']) for c in checks) else 'FAIL','actual_glb_reimport':True,'wheel_hierarchy':checks,'bounds_blender':{'min':mins,'max':maxs,'dimensions':[b-a for a,b in zip(mins,maxs)]},'aero_hinge_present':bool(bpy.data.objects.get('AeroWing_Hinge')),'socket_count':len([o for o in bpy.data.objects if o.name.startswith('Thruster_')]),'render_engine':'Cycles CPU, no denoising','limitations':manifest['limitations']}
# Geometry intersection checks are static mesh checks, not a vehicle physics claim.
bodycheck=bpy.data.objects['CarBody'];bodycheck.data.calc_loop_triangles()
bt=list(bodycheck.data.loop_triangles)
bverts=[bodycheck.matrix_world@v.co for v in bodycheck.data.vertices]
bvh=BVHTree.FromPolygons(bverts,[tuple(t.vertices) for t in bt],all_triangles=True,epsilon=0)
clearances=[]
for key in steers:
    s=bpy.data.objects['Steer_'+key];s.rotation_mode='XYZ';wh=bpy.data.objects['Wheel_'+key]
    wh.data.calc_loop_triangles()
    tiretris=[t for t in wh.data.loop_triangles if 'Tire rubber' in wh.data.materials[t.material_index].name]
    for angle in ([0,-.4,.4] if key.startswith('Front') else [0]):
        s.rotation_euler.z=angle;bpy.context.view_layer.update()
        tirebvh=BVHTree.FromPolygons([wh.matrix_world@v.co for v in wh.data.vertices],[tuple(t.vertices) for t in tiretris],all_triangles=True,epsilon=0)
        overlaps=bvh.overlap(tirebvh)
        mats={}
        for a,b in overlaps:
            mn=bodycheck.data.materials[bt[a].material_index].name;mats[mn]=mats.get(mn,0)+1
        clearances.append({'wheel':key,'steer_rad':angle,'surface_triangle_overlap_pairs':len(overlaps),'overlap_materials':mats})
    s.rotation_euler.z=0
bpy.context.view_layer.update()
# Confirm rotation actually displaces tire geometry while the caliper stays fixed.
movement=[]
for key in steers:
    sp=bpy.data.objects['Spin_'+key];sp.rotation_mode='XYZ';wh=bpy.data.objects['Wheel_'+key];cal=bpy.data.objects['Caliper_'+key]
    ix=max(range(len(wh.data.vertices)),key=lambda i:wh.data.vertices[i].co.x)
    before=wh.matrix_world@wh.data.vertices[ix].co;cal_before=cal.matrix_world.copy();hub_before=sp.matrix_world.translation.copy()
    sp.rotation_euler.y=.7;bpy.context.view_layer.update()
    after=wh.matrix_world@wh.data.vertices[ix].co
    movement.append({'wheel':key,'spin_test_rad':.7,'tire_vertex_movement_m':(after-before).length,'caliper_matrix_delta':max(abs(cal.matrix_world[r][c]-cal_before[r][c]) for r in range(4) for c in range(4)),'hub_movement_m':(sp.matrix_world.translation-hub_before).length})
    sp.rotation_euler.y=0;bpy.context.view_layer.update()
validation['wheel_rotation_tests']=movement
validation['wheel_rotation_pass']=all(m['tire_vertex_movement_m']>.1 and m['caliper_matrix_delta']<1e-6 and m['hub_movement_m']<1e-6 for m in movement)
ah=bpy.data.objects['AeroWing_Hinge'];ah.rotation_mode='XYZ';aw=bpy.data.objects['AeroWing'];wv0=aw.matrix_world@aw.data.vertices[0].co
ah.rotation_euler.y=.18;bpy.context.view_layer.update();wdelta=(aw.matrix_world@aw.data.vertices[0].co-wv0).length
ah.rotation_euler.y=0;bpy.context.view_layer.update()
validation['wing_rotation_test']={'angle_rad':.18,'wing_vertex_movement_m':wdelta,'passes':wdelta>.005}
validation['browser_budget_pass']=tri<=42000 and draws<=40
validation['static_tire_surface_checks']=clearances
validation['static_tire_check_pass']=not any(c['surface_triangle_overlap_pairs'] for c in clearances)
validation['test_note']='Static BVH tire/body surface tests only; does not assert dynamic suspension, contact or engineering accuracy.'
if not (validation['static_tire_check_pass'] and validation['wheel_rotation_pass'] and validation['browser_budget_pass'] and validation['wing_rotation_test']['passes']):validation['result']='REVIEW'
(OUT/'car_silver_validation.json').write_text(json.dumps(validation,indent=2))
# Neutral studio test renders, geometry is actual GLB round trip.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=72;scene.cycles.use_denoising=False
scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
world=bpy.data.worlds.new('Silver QA neutral studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.17,.19,.21,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;scene.world=world
floor=mat('Silver QA studio floor',(.18,.19,.205),.0,.5)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.004));bpy.context.object.data.materials.append(floor)
def aim(o,at):o.rotation_euler=(Vector(at)-o.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,power,size,color,at=(0,0,.6),size_y=None):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='RECTANGLE';d.size=size;d.size_y=size_y or size;d.color=color
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;aim(o,at)
light('Huge soft key',(1.1,4.3,6.0),1350,5.0,(1,.94,.88),size_y=3)
light('Long body strip',(-1,-4.5,3.7),1050,5.0,(.77,.86,1),size_y=1.3)
light('Rear edge strip',(-4,1.5,3.2),900,3.0,(1,.94,.84),size_y=2)
light('Front soft fill',(5,1,2.3),600,3.0,(.88,.94,1),size_y=2)
camd=bpy.data.cameras.new('Silver QA camera');cam=bpy.data.objects.new('Silver QA camera',camd);scene.collection.objects.link(cam);scene.camera=cam;camd.lens=58
for tag,loc,at in [('front',(5.8,6.7,2.65),(.12,0,.66)),('rear',(-5.7,-6.5,2.55),(-.10,0,.67))]:
    if '--no-render' in sys.argv:continue
    cam.location=loc;aim(cam,at);scene.render.filepath=str(OUT/('car_silver_preview_'+tag+'.png'));bpy.ops.render.render(write_still=True)
print('SILVER_CAR_READY',json.dumps({'manifest':str(OUT/'car_silver_manifest.json'),'triangles':tri,'draw_calls':draws,'bytes':len(blob),'validation':validation['result']}))
