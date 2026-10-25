"""Fresh reconstruction of Vermilion Butterfly GT after V12 source loss.
Original procedural interpretation of recovered user reference and prior preview.
"""
import sys,math,json,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import bpy
from mathutils import Vector
import rebuild_car_helpers as h
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/cars/vermilion';WEB=ROOT/'assets/web';PUBLIC=ROOT/'web/public/assets'
for p in(OUT,WEB,PUBLIC):p.mkdir(parents=True,exist_ok=True)
h.reset();paint=h.material('Crimson multi-coat | original fan concept',(.44,.009,.018),.62,.24,coat=.52);carbon=h.material('Vermilion | satin aero carbon',(.009,.014,.018),.22,.36);carbon['double_sided']=True
glass=h.material('Vermilion | smoke curved glazing',(.024,.043,.050),.12,.12,alpha=.38,coat=.3);alloy=h.material('Vermilion | machined forged alloy',(.24,.29,.32),.86,.24);rubber=h.material('Tire rubber | vermilion compound',(.009,.012,.014),0,.78);interior=h.material('Vermilion | charcoal suede',(.024,.027,.031),0,.84);white=h.material('Vermilion | white blade optics',(.72,.91,1),.08,.2,emit=2.2);red=h.material('LED ruby red | vermilion tail lamps',(.46,.004,.010),.1,.24,emit=.9)
root=h.empty('CAR_ROOT');body=h.empty('CarBody',parent=root);hood=h.empty('Hood',parent=body);wing=h.empty('RearWing',(-2.03,0,1.01),body);groups=[root,body,hood,wing];hinges={};doors={}
for n,s in [('Left',1),('Right',-1)]:hinges[n]=h.empty('DoorHinge_'+n,(.72,s*.72,.77),body);doors[n]=h.empty('Door_'+n,parent=hinges[n]);groups.extend((hinges[n],doors[n]))
h.CURRENT=body
rows=[(-2.37,.87,.66,.71),(-2.16,1.01,.73,.83),(-1.80,1.07,.80,.92),(-1.35,1.08,.84,.94),(-1.00,1.01,.81,.88),(-.70,.96,.76,.82),(-.20,.945,.74,.79),(.35,.95,.73,.77),(.79,1.00,.73,.81),(1.15,1.05,.68,.85),(1.45,1.065,.60,.86),(1.80,1.04,.53,.76),(2.13,.96,.48,.64),(2.33,.86,.465,.55)]
def prop(x):return h.smooth_interp(rows,x)
def top(x,y):
 w,c,f=prop(x);q=min(1.02,abs(y)/w);a=min(1,q/.80);a=a*a*(3-2*a);return c+(f-c)*a-.10*max(0,(q-.89)/.11)**1.5

def sweep(x,y):
 w,c,f=prop(x)
 if x>1.91:return x-.12*min(1,(x-1.91)/.42)*(abs(y)/w)**2
 if x<-1.95:return x+.10*min(1,(-x-1.95)/.42)*(abs(y)/w)**2
 return x
xs=[-2.37+4.70*i/88 for i in range(89)];v=[];f=[];N=36
for x in xs:
 w,c,a=prop(x);ring=[(w*(-1+2*j/28),top(x,w*(-1+2*j/28)))for j in range(29)]+[(w,a-.20),(w*.98,.34),(w*.86,.16),(0,.14),(-w*.86,.16),(-w*.98,.34),(-w,a-.20)];v.extend((sweep(x,y),y,z)for y,z in ring)
for i in range(len(xs)-1):
 for j in range(N):f.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
f.extend([tuple(reversed(range(N))),tuple((len(xs)-1)*N+j for j in range(N))]);shell=h.mesh('Vermilion flowing pointed-nose monocoque',v,f,paint,True)
tri=shell.modifiers.new('Stable boolean foundation','TRIANGULATE');h.apply_mod(shell,tri)
def cut_car(obj,cutter,name):
 idx=obj.data.materials.find(carbon.name)
 if idx<0:obj.data.materials.append(carbon);idx=len(obj.data.materials)-1
 while len(cutter.data.materials)<=idx:cutter.data.materials.append(carbon)
 for face in cutter.data.polygons:face.material_index=idx
 h.cut(obj,cutter,name)
for x in(-1.35,1.35):
 bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=.449,depth=3,location=(x,0,.368),rotation=(math.pi/2,0,0));cut_car(shell,bpy.context.object,'Real wheel arch aperture')
cut_car(shell,h.box('Temporary open cockpit',(-.19,0,1.03),(2.0,1.23,1.48),carbon,0),'Actual cockpit volume')
for s in(-1,1):
 cut_car(shell,h.box('Temporary separate side door aperture',(-.02,s*.96,.575),(1.53,.72,.59),carbon,0),'Actual door aperture')
 h.line('Carbon lower sill edge',[(.78,s*1.00,.19),(.25,s*1.025,.18),(-.85,s*1.045,.22)],.020,carbon,8)
 # Dark rear shoulder inlet and a formed trailing buttress, distinct from the canopy car.
 poly=[(-.78,.41),(-.91,.37),(-1.03,.70),(-.99,.84),(-.83,.79)];vv=[(x,y,z)for y in(s*.73,s*1.27)for x,z in poly];n=len(poly);ff=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)];cut_car(shell,h.mesh('Temporary rear shoulder inlet',vv,ff,carbon,False),'Open shoulder inlet');h.mesh('Dark recessed rear shoulder radiator',[(x,s*.72,z)for x,z in poly],[tuple(range(n))],carbon,False,normal_hint=(0,s,0))
 h.line('Sculpted red shoulder intake rim',[(-.82,s*1.00,.78),(-1.00,s*1.06,.83),(-1.10,s*1.075,.76)],.020,paint,8)
# Tapered pointed front bonnet, physically separated by its own exact boundary.
def hw(x):
 if x<1.80:return .60-.02*(x-.81)/.99
 if x<2.17:return .58-.35*(x-1.80)/.37
 return max(.001,.23*(2.28-x)/.11)
edge=[.81+1.47*i/48 for i in range(49)];outline=[(sweep(x,-hw(x)),-hw(x))for x in edge]+[(sweep(x,hw(x)),hw(x))for x in reversed(edge)];cut_car(shell,h.prism('Temporary exact bonnet aperture',outline,.36,1.6,carbon),'Separate pointed bonnet');h.CURRENT=hood

def bonnet(t,u):
 x=.81+1.47*t;y=(u*2-1)*hw(x);return(sweep(x,y),y,top(x,y)+.004)
bo=h.panel('Separate pointed red bonnet',bonnet,36,22,paint);so=bo.modifiers.new('Formed bonnet actual thickness','SOLIDIFY');so.thickness=.010
for s in(-1,1):h.line('Fine bonnet shutline',[bonnet(i/36,0 if s<0 else 1)for i in range(37)],.0022,carbon,5)
# Actual recessed twin upper bonnet apertures with separate black louvers.
h.apply_mod(bo,so)
for s in(-1,1):
 h.cut(bo,h.prism('Temporary upper bonnet vent aperture',[(.885,s*.24),(1.35,s*.24),(1.35,s*.45),(.885,s*.45)],.3,1.1,carbon),'Open bonnet cooling vent')
 h.panel('Tapered upper bonnet cooling channel',lambda t,u,sg=s:(.89+.43*t,sg*(.24+.21*u),top(.89+.43*t,sg*(.24+.21*u))-.026),18,8,carbon)
 for j in range(5):x=.93+j*.073;h.line('Bonnet louver blade',[(x,s*.25,top(x,s*.25)-.010),(x+.045,s*.44,top(x+.045,s*.44)-.010)],.006,carbon,6)
h.CURRENT=body
# Bifurcated radiators and central sculpted beak: no marque shield or emblem.
for s in(-1,1):
 poly=[(s*.075,.16),(s*.82,.18),(s*.91,.36),(s*.77,.45),(s*.11,.41)];vv=[(x,y,z)for x in(1.99,2.67)for y,z in poly];n=len(poly);ff=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)];cut_car(shell,h.mesh('Temporary split front radiator',vv,ff,carbon,False),'Actual split front intake');h.mesh('Recessed dark front radiator',[(2.00,y,z)for y,z in poly],[tuple(range(n))],carbon,False,normal_hint=(1,0,0))
 for j in range(6):y=s*(.16+.11*j);h.line('Subtle front radiator web',[(2.025,y,.19),(2.025,y,.39)],.004,carbon,5)
 h.line('Front sculpted lower red intake lip',[(2.34,s*.08,.15),(2.26,s*.67,.16),(2.13,s*.91,.20)],.018,paint,8)
 h.prism('Split carbon front aero blade',[(2.40,s*.04),(2.32,s*.66),(2.17,s*1.00),(1.97,s*.98),(2.08,s*.65),(2.26,s*.04)],.105,.136,carbon)
 # Long swept blade lamp housings follow the crowned fender, with bent light guides.
 def lamp(t,u,sg=s):
  x=1.16+.85*t;y=sg*(.83+.035*math.sin(math.pi*t)+(.075-.015*t)*(u*2-1));return(sweep(x,y),y,top(x,y)+.014)
 h.panel('Swept sculpted blade lamp well',lamp,26,7,carbon)
 pts=[]
 for j in range(34):
  t=j/33;x=1.17+.83*t;y=s*(.90+.025*math.sin(math.pi*t)-.10*max(0,(t-.75)/.25));pts.append((sweep(x,y),y,top(x,y)+.025))
 h.line('Long bent white light blade',pts,.006,white,7)
 for x in(1.57,1.75):y=s*.84;z=top(x,y)+.023;h.torus('Blade lamp optical bezel',(sweep(x,y),y,z),.025,.004,alloy,'Z',24,5);h.cylinder('Blade lamp projector lens',(sweep(x,y),y,z+.004),.017,.005,white,'Z',24)
# Low black canopy and actual articulated door components.
def wind(t,u):
 q=u*2-1;return(.74-.86*t,q*(.60-.09*t),(.755-.022*q*q)*(1-t)+(1.185-.045*q*q)*t+.030*math.sin(math.pi*t))
def roof(t,u):
 q=u*2-1;return(-.12-.78*t,q*(.51-.06*t),1.185+.023*math.sin(math.pi*t)-.035*t-.045*q*q)
def aft(t,u):
 q=u*2-1;return(-.90-.50*t,q*(.45-.11*t),(1.150-.045*q*q)*(1-t)+(.850-.018*q*q)*t)
h.panel('Curved sports windshield',wind,20,24,glass);h.panel('Black sports roof canopy',roof,20,20,carbon);h.panel('Rear powertrain glazing',aft,18,20,glass);h.line('Windshield base seal',[wind(0,i/32)for i in range(33)],.008,carbon,7)
for name,s in [('Left',1),('Right',-1)]:
 h.CURRENT=doors[name]
 def upper(t):return Vector(wind(t/.55,0 if s<0 else 1))if t<.55 else Vector(roof((t-.55)/.45,0 if s<0 else 1))
 def base(t):return Vector((.73-1.50*t,s*(.64+.035*math.sin(math.pi*t)),.735+.060*t))
 def side(t,u):
  p=base(t)*(1-u)+upper(t)*u;p.y+=s*.012*math.sin(math.pi*t)*math.sin(math.pi*u);return p
 h.panel('Butterfly door side glazing '+name,side,28,12,glass,normal_hint=(0,s,.2))
 for u in(0,1):h.line('Door glazing fine seal '+name,[side(i/32,u)for i in range(33)],.008,carbon,7)
 h.line('Door rear glazing edge '+name,[side(1,i/16)for i in range(17)],.008,carbon,7)
 def skin(t,u):return(.73-1.50*t,s*(.944+.018*math.sin(math.pi*t)),(.305+.015*t)*(1-u)+(.735+.060*t+.018*math.sin(math.pi*t))*u)
 do=h.panel('Separate red butterfly door shell '+name,skin,28,12,paint,normal_hint=(0,s,.1));so=do.modifiers.new('Door actual composite shell thickness','SOLIDIFY');so.thickness=.018
 def belt(t,u):return base(t)*(1-u)+Vector(skin(t,1))*u
 do=h.panel('Swept butterfly door shoulder '+name,belt,26,9,paint,normal_hint=(0,s,.7));so=do.modifiers.new('Shoulder skin thickness','SOLIDIFY');so.thickness=.012
 for t in(0,1):h.line('Door fine vertical shutline '+name,[skin(t,i/14)for i in range(15)],.0026,carbon,5)
 h.line('Door lower shutline '+name,[skin(i/28,0)for i in range(29)],.0026,carbon,5);h.box('Flush unbranded door latch '+name,(-.40,s*.968,.672),(.10,.014,.022),carbon,.007)
 h.line('Mirror aerodynamic stalk '+name,[(.30,s*.68,.82),(.36,s*.99,.87)],.011,carbon,7);pod=h.box('Painted mirror housing '+name,(.37,s*1.06,.90),(.21,.13,.075),paint,.028);pod.rotation_euler.z=s*.15;h.box('Mirror reflective face '+name,(.264,s*1.06,.90),(.008,.10,.05),glass,.014)
h.CURRENT=body
for s in(-1,1):
 def sail(t,u,sg=s):
  a=Vector((-.90+.13*t,sg*(.45+.19*t),1.105-.31*t));b=Vector((-1.40,sg*.34,.832));return a*(1-u)+b*u
 p=h.panel('Filled sculpted rear canopy buttress',sail,16,12,paint,normal_hint=(0,s,.5));so=p.modifiers.new('Rear buttress true thickness','SOLIDIFY');so.thickness=.012
h.line('Slim windshield wiper',[wind(.04,.25),wind(.09,.70)],.0045,carbon,6);h.cockpit(paint,carbon,glass,alloy,interior,white)
# Rear cooling deck, round independent lamps and open fictional boost outlets.
for s in(-1,1):
 h.panel('Rear engine-deck dark channel',lambda t,u,sg=s:(-1.40-.62*t,sg*(.37+.22*u),top(-1.40-.62*t,sg*(.37+.22*u))+.012),18,7,carbon)
 for j in range(7):x=-1.46-j*.074;h.line('Rear deck louver',[(x,s*.38,top(x,s*.38)+.022),(x-.03,s*.58,top(x-.03,s*.58)+.022)],.006,carbon,6)
 cx=sweep(-2.37,s*.66);cut_car(shell,h.cylinder('Temporary inset round rear lamp aperture',(cx,s*.66,.62),.083,.24,carbon,'X',48),'Actually recessed rear lamp housing');h.cylinder('Flush rear lamp recessed dark housing',(cx+.025,s*.66,.62),.080,.036,carbon,'X',40);h.torus('Flush round red rear light guide',(cx-.007,s*.66,.62),.065,.011,red,'X',40,8);h.cylinder('Rear lamp dark optical center',(cx-.001,s*.66,.62),.045,.008,carbon,'X',32)
 h.cylinder('Boost outlet recessed dark back',(-2.317,s*.56,.255),.072,.016,carbon,'X',32);h.torus('Open boost outlet machined lip',(-2.40,s*.56,.255),.076,.0065,alloy,'X',32,6);vv=[(x,s*.56+.072*math.cos(2*math.pi*j/32),.255+.072*math.sin(2*math.pi*j/32))for x in(-2.40,-2.325)for j in range(32)];ff=[(j,j+32,(j+1)%32+32,(j+1)%32)for j in range(32)];h.mesh('Open boost tube inner wall',vv,ff,carbon,True)
 h.line('Outer rear carbon diffuser lip',[(-2.40,s*.90,.17),(-2.15,s*.93,.14),(-1.96,s*.88,.18)],.018,carbon,8)
h.panel('Curved rear dark radiator fascia',lambda t,u:(sweep(-2.37,(t*2-1)*.84)-.015,(t*2-1)*.84,.38+.19*u),26,7,carbon,normal_hint=(-1,0,0))
h.panel('Curved rear diffuser carbon surround',lambda t,u:(sweep(-2.37,(t*2-1)*.82)-.016,(t*2-1)*.82,.145+.23*u),24,8,carbon,normal_hint=(-1,0,0))
for y in(-.68,-.42,-.20,0,.20,.42,.68):h.mesh('Rear diffuser fin',[(-2.40,y,.13),(-1.95,y,.14),(-2.03,y,.35),(-2.38,y,.35)],[(0,1,2,3)],carbon,False,normal_hint=(0,1,0))
h.CURRENT=wing
for s in(-1,1):h.box('Fixed rear wing support',(-2.05,s*.53,.92),(.13,.035,.28),carbon,.012)
p=h.panel('Fixed sculpted rear wing',lambda t,u:(-2.24+.35*t+.07*(u*2-1)**2,(u*2-1)*.99,1.083+.020*math.sin(math.pi*t)-.012*(u*2-1)**2),9,18,carbon);so=p.modifiers.new('Wing actual thickness','SOLIDIFY');so.thickness=.014
for s in(-1,1):h.box('Red rear wing end plate',(-2.01,s*.995,1.075),(.34,.022,.10),paint,.016)
w=h.build_wheels(root,groups,paint,alloy,rubber,prefix='Vermilion',lateral=.924,spokes=5);h.CURRENT=None;bpy.context.view_layer.update();root['vehicle']='Reconstructed Vermilion Butterfly GT';root['provenance']='New original geometry rebuilt after source loss; not previous V12 bytes.'
native=OUT/'vermilion.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native));m={'asset':'Vermilion Butterfly GT','vehicle_id':'vermilion','reconstruction':True,'coordinates':'metres; +X forward,+Y up,-Z left','car_root':'CAR_ROOT','body_mesh':'CarBody','paint_material':paint.name,'glass_material':glass.name,'wheelbase_m':2.7,'wheel_radius_m':.366,'wheel_centers_three':{k:[o.location.x,o.location.z,-o.location.y]for k,o in w['steers'].items()},'steer_nodes':['Steer_'+k for k in w['steers']],'spin_nodes':['Spin_'+k for k in w['steers']],'steer_axis':'Three local +Y','spin_axis_for_forward':'Three local -Z','max_visual_steer_rad':None,'chassis_pose_limits':{'roll_rad':.008,'pitch_rad':.005,'heave_m':.002},'boost_mounts_three_m':[[-2.4,.255,-.56],[-2.4,.255,.56]],'wing_type':'Fixed RearWing, not AeroWing_Hinge','door_hinges':{'Left':{'name':'DoorHinge_Left','native_axis':[-.45,1,0]},'Right':{'name':'DoorHinge_Right','native_axis':[.45,1,0]}},'door_opening_status':'Separate articulated geometry supplied; opening clearance not yet validated. Runtime defaults closed.','source':'assets/cars/vermilion/vermilion.blend','source_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),'generator':'blender/build_vermilion.py','rights':'No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses.','provenance':'Original reconstructed geometry/materials. References inform silhouette only; no logos or image textures embedded. Not a licensed replica or exact prior source recovery.','status':'Generated; visual and exported-geometry QA pending.'};m=h.export_glb(groups,WEB/'car_vermilion.glb',m)
for p in(OUT/'manifest.json',WEB/'car_vermilion_manifest.json'):p.write_text(json.dumps(m,indent=2))
shutil.copy2(WEB/'car_vermilion.glb',PUBLIC/'car_vermilion.glb');print('VERMILION_REBUILT',json.dumps(m),flush=True)
