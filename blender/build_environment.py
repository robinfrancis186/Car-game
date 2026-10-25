"""Original procedural Kerala coastal prop library. Blender 4.3.2.
Run: blender -b --factory-startup -t 4 --python blender/build_environment.py
All modeled geometry original; dimensions are artistic, not a survey.
"""
import bpy, math, random, json, os, sys
from mathutils import Vector
from math import sin, cos, pi
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'/'environment'
for d in ('exports','textures','previews'): (OUT/d).mkdir(parents=True,exist_ok=True)
random.seed(1022)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
base=bpy.data.collections.get('Collection'); base.name='Environment_Library'
ASSETS={}; current=None

def mat(name,color,rough=.6,metal=0,noise=0,bump=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes; p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    if noise:
        t=n.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=noise;t.inputs['Detail'].default_value=3
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[0].color=(*(v*.55 for v in color),1);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(*(min(1,v*1.25) for v in color),1)
        m.node_tree.links.new(t.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
        if bump:
            b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.04;m.node_tree.links.new(t.outputs['Fac'],b.inputs['Height']);m.node_tree.links.new(b.outputs[0],p.inputs['Normal'])
    return m
M={
 'bark':mat('Palm_Bark_WarmGray',(.26,.21,.13),.9,noise=8,bump=.3),
 'ring':mat('Palm_Ring_Scars',(.30,.26,.18),.92),
 'leaf':mat('Coconut_Leaf_Emerald',(.075,.24,.026),.48),
 'leafLight':mat('Coconut_Leaf_Sunlit',(.18,.34,.048),.5),
 'leafDark':mat('Coconut_Leaf_Shadow',(.034,.14,.018),.6),
 'stem':mat('Coconut_Frond_Stem',(.23,.32,.055),.65),
 'coconut':mat('Coconut_GreenGold',(.32,.40,.12),.8,noise=15,bump=.12),
 'plaster':mat('House_WarmLime_Plaster',(.78,.70,.49),.85,noise=5,bump=.12),
 'cream':mat('House_Trim_Cream',(.92,.85,.64),.7),
 'wood':mat('House_Teak_Wood',(.16,.068,.026),.48,noise=9,bump=.18),
 'glass':mat('House_Window_Glass',(.045,.14,.15),.18,metal=.45),
 'foundation':mat('House_Stone_Plinth',(.26,.25,.20),.9,noise=12,bump=.35),
 'tile':mat('Roof_Terracotta',(.39,.105,.037),.75,noise=5,bump=.14),
 'tile2':mat('Roof_Terracotta_Warm',(.53,.19,.075),.78),
 'tile3':mat('Roof_Terracotta_Dark',(.25,.066,.028),.8),
 'roofbase':mat('Roof_Underlay',(.13,.055,.025),.9),
 'blue':mat('Boat_Coastal_Teal',(.025,.30,.31),.55,noise=4,bump=.15),
 'yellow':mat('Boat_Saffron_Stripe',(.95,.48,.025),.48),
 'rope':mat('Boat_Coir_Rope',(.36,.24,.105),.95),
 'sand':mat('Beach_Warm_Sand',(.68,.56,.34),.95,noise=80,bump=.2),
 'water':mat('ArabianSea_Teal',(.025,.20,.22),.18,metal=.2,noise=2,bump=.3),
 'asphalt':mat('Road_Asphalt',(.07,.078,.075),.9,noise=90,bump=.3),
 'stripe':mat('Road_OffWhite_Marking',(.85,.82,.67),.8),
 'gravel':mat('Road_Shoulder_Gravel',(.31,.24,.15),.9,noise=45,bump=.35),
 'black':mat('Road_Furniture_Black',(.022,.028,.03),.65),
 'white':mat('Road_Furniture_White',(.83,.84,.77),.5),
 'reflector':mat('Road_Red_Reflector',(.8,.025,.01),.2,metal=.1),
 'grass':mat('Ground_Tropical_Grass',(.14,.23,.035),.9),
 'rock':mat('SeaWall_Granite',(.19,.21,.18),.9,noise=7,bump=.5)
}

def asset(name,desc):
    global current
    c=bpy.data.collections.new(name);base.children.link(c)
    e=bpy.data.objects.new(name+'_ROOT',None);c.objects.link(e)
    current={'collection':c,'root':e,'description':desc,'objects':[]};ASSETS[name]=current
    return e

def reg(o,name,m=None):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    current['collection'].objects.link(o);o.parent=current['root'];current['objects'].append(o)
    if m:o.data.materials.append(M[m] if isinstance(m,str) else m)
    return o

def mesh(name,vs,fs,m,smooth=False):
    d=bpy.data.meshes.new(name+'_Mesh');d.from_pydata(vs,[],fs);d.update()
    o=bpy.data.objects.new(name,d);reg(o,name,m)
    if smooth:
        for p in d.polygons:p.use_smooth=True
    return o

def cube(name,loc,scale,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);reg(o,name,m)
    if bevel:
        mod=o.modifiers.new('Soft_Edges','BEVEL');mod.width=min(bevel,min(scale)*.24);mod.segments=2
        mod=o.modifiers.new('Weighted_Normals','WEIGHTED_NORMAL')
    return o

def uv(name,loc,scale,m,segments=16,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);reg(o,name,m)
    for p in o.data.polygons:p.use_smooth=True
    return o

def tube(name,pts,radii,m,sides=10):
    vs=[];fs=[];previous_binormal=None
    for i,p in enumerate(pts):
        p=Vector(p);t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)])
        t.normalize()
        if previous_binormal is None:
            reference=Vector((1,0,0)) if abs(t.z)>.9 else Vector((0,0,1))
            b=t.cross(reference)
        else:
            b=previous_binormal-t*previous_binormal.dot(t)
        if b.length<1e-6:b=t.cross(Vector((0,1,0)))
        b.normalize();n=t.cross(b).normalized();previous_binormal=b.copy()
        for j in range(sides):vs.append(tuple(p+radii[i]*(cos(j*2*pi/sides)*b+sin(j*2*pi/sides)*n)))
    for i in range(len(pts)-1):
        for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
    fs.append(tuple(range(sides-1,-1,-1)));fs.append(tuple((len(pts)-1)*sides+j for j in range(sides)))
    return mesh(name,vs,fs,m,True)

def beam(name,a,b,w,m):return tube(name,[a,b],[w,w],m,8)

def leaf_mesh(name,points,widths,m):
    vs=[];fs=[]
    for i,p in enumerate(points):
        p=Vector(p);t=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)]);n=t.cross(Vector((0,0,1))).normalized()
        vs.extend([tuple(p-n*widths[i]),tuple(p+Vector((0,0,.018))),tuple(p+n*widths[i])])
    for i in range(len(points)-1):
        a=i*3;fs.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
    return mesh(name,vs,fs,m,True)

def palm(name,h,lean,seed):
    rng=random.Random(seed);asset(name,'Original coconut palm; meter units; ground root; curved ringed trunk, modeled fronds, coconuts.')
    def center(t):return Vector((lean*t*t,.22*sin(t*pi),h*t))
    pts=[center(i/40) for i in range(41)];rr=[.24*(1-i/50)+.08 for i in range(41)]
    tube(name+'_Trunk',pts,rr,'bark',18)
    # visible ring scars modeled, not just shader texture
    vs=[];fs=[]
    for i in range(1,int(h/.16)):
        t=i*.16/h;c=center(t);r=.24*(1-t*.8)+.082
        start=len(vs)
        for k in range(2):
            for j in range(18):
                a=j*2*pi/18;vs.append(tuple(c+Vector((cos(a)*r,sin(a)*r,(k-.5)*.026))))
        for j in range(18):fs.append((start+j,start+(j+1)%18,start+18+(j+1)%18,start+18+j))
    mesh(name+'_Trunk_LeafScars',vs,fs,'ring',True)
    top=center(1)
    for i in range(18):
        ang=i*2*pi/18+rng.uniform(-.12,.12);direction=Vector((cos(ang),sin(ang),0));side=Vector((-sin(ang),cos(ang),0))
        length=rng.uniform(3.5,4.5);elev=rng.uniform(.6,1.3) if i<12 else rng.uniform(1.3,2.1)
        droop=rng.uniform(1.4,2.1) if i<12 else rng.uniform(.6,1.2)
        def path(t):return top+direction*(t*length)+Vector((0,0,elev*sin(t*pi*.83)-droop*t*t))
        spine=[path(t/12) for t in range(13)];tube(name+f'_FrondStem_{i:02}',spine,[.045*(1-t/13) for t in range(13)],'stem',6)
        # paired narrow, ribbed pinnae; leaf size tapers at both ends
        leaves_vs=[];leaves_fs=[]
        for j in range(2,32):
            t=j/33;p=path(t);size=(sin(t*pi)**.65)*rng.uniform(.65,1.1)
            for sign in (-1,1):
                off=side*sign;points=[];widths=[]
                for k in range(5):
                    u=k/4;points.append(p+off*size*u+direction*(.25*u+.1*u*u)+Vector((0,0,-.24*u*u+.07*sin(u*pi))));widths.append(.042*(sin(u*pi)**.6) if k else .019)
                # append joined leaf topology to reduce object count
                start=len(leaves_vs)
                for k,q in enumerate(points):
                    tangent=points[min(k+1,4)]-points[max(0,k-1)];n=tangent.cross(Vector((0,0,1))).normalized();leaves_vs.extend([tuple(q-n*widths[k]),tuple(q+Vector((0,0,.012))),tuple(q+n*widths[k])])
                for k in range(4):
                    a=start+k*3;leaves_fs.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
        mesh(name+f'_FrondLeaflets_{i:02}',leaves_vs,leaves_fs, ['leaf','leafLight','leafDark'][i%3],True)
    for i in range(11):
        a=i*2*pi/7;c=top+Vector((.32*cos(a),.32*sin(a),-.25-(i//7)*.25));uv(name+f'_Coconut_{i:02}',c,(.14,.14,.20),'coconut')
    # compact fresh crown spear
    for i in range(3):
        a=i*2*pi/3;leaf_mesh(name+f'_CrownSpear_{i}',[top,top+Vector((.25*cos(a),.25*sin(a),.8)),top+Vector((.5*cos(a),.5*sin(a),1.65))],[.04,.12,0],'leafLight')

palm('CoconutPalm_A',8.2,1.3,8)
palm('CoconutPalm_B',6.4,-.8,11)

# Kerala-inspired lime-plaster home, large clay-tile overhang, timber veranda.
asset('KeralaHouse','Original Kerala-inspired coastal home, terracotta roof with modeled tiles, timber veranda, shutters and plinth. Ground root.')
cube('House_Plinth',(0,0,.28),(8.6,6.5,.56),'foundation',.06)
cube('House_MainWalls',(0,.3,1.78),(7.8,4.7,2.6),'plaster',.035)
cube('House_LowerTrim',(0,.3,.65),(7.9,4.8,.13),'cream',.02)
cube('House_VerandaFloor',(0,-2.65,.61),(8.1,1.5,.16),'foundation',.03)
for x in (-3.7,-1.25,1.25,3.7):
    cube(f'Veranda_Column_{x}',(x,-3.15,1.85),(.19,.19,2.5),'wood',.018)
    cube(f'Veranda_ColumnBase_{x}',(x,-3.15,.77),(.31,.31,.25),'cream',.02)
    for sign in (-1,1):beam(f'Veranda_Brace_{x}_{sign}',(x,-3.15,2.5),(x+sign*.5,-3.15,2.98),.055,'wood')
cube('Veranda_FrontLintel',(0,-3.15,3.02),(8.3,.19,.22),'wood',.02)
for i in range(3):cube(f'Veranda_Step_{i}',(0,-3.65-i*.27,.49-i*.14),(2.15,.6,.16),'foundation',.025)
# gable infills and roof underlay
verts=[(-3.9,-2.05,3.08),(-3.9,2.65,3.08),(-3.9,.3,4.45),(3.9,-2.05,3.08),(3.9,2.65,3.08),(3.9,.3,4.45)]
mesh('House_GableWalls',verts,[(0,1,2),(3,5,4)],'plaster')
roof_vs=[(-4.5,-3.7,2.98),(4.5,-3.7,2.98),(-4.5,.3,4.56),(4.5,.3,4.56),(-4.5,3.3,3.12),(4.5,3.3,3.12)]
mesh('House_Roof_Underlay',roof_vs,[(0,1,3,2),(2,3,5,4)],'roofbase')
# each overlapping tile segment has slightly convex profile and lip
for side,end_y,end_z,rows in [(-1,-3.75,2.99,15),(1,3.35,3.1,12)]:
    vs=[];fs=[];matids=[]
    for row in range(rows):
        ta=row/rows;tb=min(1,(row+1.22)/rows);ya=.3+(end_y-.3)*ta;yb=.3+(end_y-.3)*tb;za=4.59+(end_z-4.59)*ta;zb=4.59+(end_z-4.59)*tb
        for col in range(40):
            x=-4.5+col*.225;start=len(vs);bias=random.uniform(-.008,.008)
            for qy,qz in ((ya,za),(yb,zb)):
                for k in range(5):vs.append((x+k*.225/4,qy,qz+.026*sin(k*pi/4)+bias))
            for k in range(4):fs.append((start+k,start+k+1,start+6+k,start+5+k));matids.append(random.choices([0,1,2],[.7,.22,.08])[0])
    o=mesh('Roof_Tiles_Front' if side<0 else 'Roof_Tiles_Back',vs,fs,'tile',True);o.data.materials.append(M['tile2']);o.data.materials.append(M['tile3'])
    for p,idx in zip(o.data.polygons,matids):p.material_index=idx
# ridge cap segments half-cylinder profile
vs=[];fs=[]
for n in range(27):
    x=-4.55+n*.34;start=len(vs)
    for xx in (x,x+.38):
        for j in range(9):a=j*pi/8;vs.append((xx,.3+.15*cos(a),4.57+.15*sin(a)))
    for j in range(8):fs.append((start+j,start+9+j,start+10+j,start+1+j))
mesh('Roof_Ridge_Caps',vs,fs,'tile2',True)
for y,z in ((-3.73,2.98),(3.33,3.1)):cube(f'Roof_EaveFascia_{y}',(0,y,z),(9.15,.12,.17),'wood',.01)
# front door framed timber panels and windows
cube('Door_Frame',(0,-2.075,1.64),(1.36,.16,2.2),'wood',.02)
cube('Door_Panel',(0,-2.172,1.61),(1.14,.06,1.98),'wood',.018)
for x in (-.27,.27):
    for z in (1.12,1.98):cube(f'Door_Inset_{x}_{z}',(x,-2.211,z),(.44,.035,.68),'roofbase',.015)
uv('Door_BrassHandle',(.42,-2.26,1.52),(.035,.035,.035),'yellow',12,6)
for x in (-2.35,2.35):
    cube(f'Window_Frame_{x}',(x,-2.10,1.95),(1.52,.18,1.55),'wood',.025)
    cube(f'Window_Glass_{x}',(x,-2.205,1.95),(1.30,.03,1.32),'glass',.01)
    for off in (-.43,0,.43):cube(f'Window_Mullion_{x}_{off}',(x+off,-2.24,1.95),(.045,.05,1.34),'wood',.006)
    cube(f'Window_Horizontal_{x}',(x,-2.24,1.95),(1.3,.05,.05),'wood',.006)
    cube(f'Window_Sill_{x}',(x,-2.22,1.13),(1.7,.35,.1),'cream',.02)
    for s in (-1,1):
        shutter=cube(f'Window_Shutter_{x}_{s}',(x+s*1.04,-2.1,1.95),(.52,.10,1.44),'wood',.01);shutter.rotation_euler.z=s*.22
        for j in range(7):cube(f'Shutter_Louvre_{x}_{s}_{j}',(x+s*1.04,-2.17,1.4+j*.17),(.45,.06,.045),'roofbase',.006)
# vertical timber gable details
for x in (-4.0,4.0):
    beam(f'Gable_Rafter_L_{x}',(x,-3.7,2.96),(x,.3,4.53),.075,'wood');beam(f'Gable_Rafter_R_{x}',(x,.3,4.53),(x,3.32,3.1),.075,'wood')
    beam(f'Gable_Center_{x}',(x,.3,3.1),(x,.3,4.5),.06,'wood')
# clay pots beside veranda
for i,x in enumerate((-3.2,3.2)):
    uv(f'House_ClayPot_{i}',(x,-2.75,.92),(.24,.24,.31),'tile2')
    for j in range(8):
        a=j*pi/4;leaf_mesh(f'House_PotLeaf_{i}_{j}',[(x,-2.75,1.1),(x+.16*cos(a),-2.75+.16*sin(a),1.5),(x+.38*cos(a),-2.75+.38*sin(a),1.36)],[.02,.05,0],'leaf')

# Traditional-inspired small beach fishing boat.
asset('FishingBoat','Original timber coastal fishing boat, teal hull and saffron gunwale; beach-static prop, not a simulated vessel.')
vs=[];fs=[];N=30;K=12
for i in range(N+1):
    u=i/N;x=-3.1+6.2*u;w=.86*(sin(pi*u)**.65)+.025;raise_end=.3*(abs(2*u-1)**3)
    for j in range(K+1):
        a=-pi/2+pi*j/K;y=w*sin(a);z=.18+.7*(1-cos(a))+raise_end
        vs.append((x,y,z))
for i in range(N):
    for j in range(K):a=i*(K+1)+j;fs.append((a,a+K+1,a+K+2,a+1))
o=mesh('Boat_Hull',vs,fs,'blue',True);sol=o.modifiers.new('Hull_Thickness','SOLIDIFY');sol.thickness=.055
for sign in (-1,1):
    p=[]
    for i in range(N+1):u=i/N;p.append((-3.1+6.2*u,sign*(.86*(sin(pi*u)**.65)+.025),.91+.3*(abs(2*u-1)**3)))
    tube('Boat_Gunwale_'+str(sign),p,[.065]*(N+1),'yellow',8)
for i,x in enumerate((-1.85,-.8,.35,1.45)):
    w=.86*(sin(pi*((x+3.1)/6.2))**.65)
    cube(f'Boat_Seat_{i}',(x,0,.73),(.32,w*1.8,.10),'wood',.035)
for j in range(7):
    x=-2.4+j*.8;w=.86*(sin(pi*((x+3.1)/6.2))**.65)
    pts=[]
    for k in range(9):a=-pi/2+pi*k/8;pts.append((x,w*sin(a)*.96,.25+.64*(1-cos(a))+.3*(abs(x/3.1)**3)))
    tube(f'Boat_InternalRib_{j}',pts,[.025]*9,'wood',6)
# weathered floor slats
for j in range(5):cube(f'Boat_FloorPlank_{j}',(0,(j-2)*.16,.42),(3.4,.14,.07),'wood',.015)
# two oars crossing interior
for i in range(2):
    a=(-1.7,-.55+i*.4,.94);b=(1.6,.35+i*.35,1.08);beam(f'Boat_OarShaft_{i}',a,b,.026,'wood')
    o=cube(f'Boat_OarBlade_{i}',(1.92,.43+i*.35,1.10),(.68,.18,.045),'wood',.045);o.rotation_euler.z=.27
# coiled rope modeled curve
pts=[]
for i in range(150):a=i*.22;r=.10+.0018*i;pts.append((-1.3+r*cos(a),r*sin(a),.82+.015*sin(a*2)))
tube('Boat_CoirRope_Coil',pts,[.018]*len(pts),'rope',5)

asset('RoadReflector','Indian roadside black-white delineator with red reflector, ground pivot.')
cube('Reflector_Post',(0,0,.56),(.12,.12,1.12),'white',.02)
cube('Reflector_BlackBand',(0,0,.84),(.125,.125,.27),'black',.005)
cube('Reflector_RedFront',(.067,0,.87),(.014,.07,.10),'reflector',.008)
cube('Reflector_RedBack',(-.067,0,.87),(.014,.07,.10),'reflector',.008)

asset('RoadSegment','20 m straight modular two-lane asphalt segment, 6.6 m paved width, 0.75 m gravel shoulder; center root, ground height z=0.')
cube('Road_Asphalt',(0,0,-.09),(20,6.6,.18),'asphalt',.02)
for s in (-1,1):
    cube('Road_Shoulder_'+str(s),(0,s*3.675,-.12),(20,.75,.18),'gravel',.02)
    cube('Road_EdgeLine_'+str(s),(0,s*3.05,.006),(20,.10,.012),'stripe')
for i in range(4):cube(f'Road_CenterDash_{i}',(-8+i*5,0,.008),(2.5,.10,.014),'stripe')

asset('BeachSandPatch','40x40m ground patch with subtle modeled undulation; stylized coastal sand.')
vs=[];fs=[];n=32
for i in range(n+1):
    for j in range(n+1):x=-20+40*i/n;y=-20+40*j/n;vs.append((x,y,-.15+.045*sin(x*.7)*sin(y*.43)))
for i in range(n):
    for j in range(n):a=i*(n+1)+j;fs.append((a,a+n+1,a+n+2,a+1))
mesh('Beach_Sand_Surface',vs,fs,'sand',True)

asset('OceanPatch','40x40m mesh surface for scene composition; not a water simulation. Procedural Blender material requires recreation in Unreal.')
vs=[];fs=[];n=64
for i in range(n+1):
    for j in range(n+1):x=-20+40*i/n;y=-20+40*j/n;vs.append((x,y,.065*sin(y*1.1+x*.15)+.025*sin(x*1.7-y*.5)))
for i in range(n):
    for j in range(n):a=i*(n+1)+j;fs.append((a,a+n+1,a+n+2,a+1))
mesh('Ocean_Surface',vs,fs,'water',True)

asset('TropicalGrass','Low clump of broad tropical roadside grass, modeled leaves; ground pivot.')
for i in range(40):
    a=random.uniform(0,pi*2);r=random.uniform(0,.22);h=random.uniform(.25,.65);p=Vector((r*cos(a),r*sin(a),0));d=Vector((cos(a),sin(a),0))
    leaf_mesh(f'Grass_Blade_{i}',[p,p+d*.06+Vector((0,0,h*.7)),p+d*.2+Vector((0,0,h)),p+d*.36+Vector((0,0,h*.68))],[.015,.025,.02,0],'grass')

asset('SeaWallRock','Irregular original granite boulder for seawalls and roadside scatter; ground pivot.')
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(0,0,.36));o=bpy.context.object
for v in o.data.vertices:v.co.x*=random.uniform(.8,1.2)*.8;v.co.y*=random.uniform(.8,1.2)*.65;v.co.z*=random.uniform(.85,1.12)*.5
reg(o,'Granite_Boulder','rock');mod=o.modifiers.new('Soft_Boulder_Edges','BEVEL');mod.width=.035;mod.segments=2

# Export originals at clean root transforms. Only geometry and root nodes.
manifest={'asset_version':1,'generator':'blender/build_environment.py','blender':bpy.app.version_string,'units':'meters','axes':'X forward, Y left, Z up. FBX export uses -Z forward/Y up conversion.','license':'Original generated geometry and textures. No project-wide reuse license has been selected for original project material; third-party components retain their stated licenses. No third-party meshes.','materials_note':'GLB carries Principled base PBR values; Blender procedural noise and bump are not baked. Recreate procedural surfaces or use the included material palette in Unreal.','assets':{}}
for name,a in ASSETS.items():
    bpy.ops.object.select_all(action='DESELECT');a['root'].select_set(True)
    for o in a['objects']:o.select_set(True)
    bpy.context.view_layer.objects.active=a['objects'][0]
    # Apply modifiers so exports are exactly the reviewed modeled shape.
    for o in a['objects']:
        bpy.context.view_layer.objects.active=o
        for mod in list(o.modifiers):
            try:bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as exc:print('MODIFIER_WARNING',o.name,exc)
    coords=[o.matrix_world@Vector(c) for o in a['objects'] for c in o.bound_box]
    lo=[min(p[k] for p in coords) for k in range(3)];hi=[max(p[k] for p in coords) for k in range(3)]
    bpy.ops.export_scene.fbx(filepath=str(OUT/'exports'/f'{name}.fbx'),use_selection=True,object_types={'MESH','EMPTY'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',bake_space_transform=False,use_mesh_modifiers=True,add_leaf_bones=False,path_mode='AUTO')
    bpy.ops.export_scene.gltf(filepath=str(OUT/'exports'/f'{name}.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT')
    manifest['assets'][name]={'description':a['description'],'root':a['root'].name,'bounds_m':{'min':lo,'max':hi},'dimensions_m':[hi[k]-lo[k] for k in range(3)],'mesh_count':len(a['objects']),'triangle_count':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in a['objects']),'fbx':f'exports/{name}.fbx','glb':f'exports/{name}.glb','mesh_names':[o.name for o in a['objects']]}
manifest['materials']={m.name:{'base_color':list(m.diffuse_color),'roughness':m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value,'metallic':m.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value} for m in M.values()}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))

# Separate presentation scene: all source assets preserved hidden; linked instances
# are positioned for a coherent small coastal roadside diorama, never baked into originals.
base.hide_render=True
staging=bpy.data.collections.new('Presentation_Only');bpy.context.scene.collection.children.link(staging)
def inst(name,pos,rot=0,scale=1):
    o=bpy.data.objects.new(name+'_Instance',None);staging.objects.link(o);o.instance_type='COLLECTION';o.instance_collection=ASSETS[name]['collection'];o.location=pos;o.rotation_euler.z=rot;o.scale=(scale,)*3;return o
# collection hide_render also hides instances, so leave collection renderable and originals move to hidden scene
base.hide_render=False
library_scene=bpy.data.scenes.new('Asset_Library');library_scene.collection.children.link(base);bpy.context.scene.collection.children.unlink(base)
inst('BeachSandPatch',(0,0,-.09),scale=1.4)
inst('RoadSegment',(0,-3.5,0),scale=1)
inst('RoadSegment',(-20,-3.5,0));inst('RoadSegment',(20,-3.5,0))
inst('KeralaHouse',(0,6,0),0)
inst('CoconutPalm_A',(-7,5,0),.4)
inst('CoconutPalm_A',(9,7,0),2.1,.95)
inst('CoconutPalm_B',(7,-10,0),-.5)
inst('CoconutPalm_A',(-11,-11,0),1.6,.85)
inst('FishingBoat',(1,-12.3,-.05),.28)
inst('OceanPatch',(0,-47,-.34),scale=1.5)
for x in range(-16,20,5):inst('RoadReflector',(x,-7.4,0),pi/2)
for x,y in [(-5,3),(5,3),(8,4),(9,-9),(-8,-9),(-7,4),(-12,6),(11,8),(-14,-9),(3,-8)]:inst('TropicalGrass',(x,y,0),random.random()*pi*2,random.uniform(.7,1.3))
for x in range(-24,25,2):inst('SeaWallRock',(x,-16.2,-.1),random.random()*6,random.uniform(.8,1.3))
# faint shoreline foam ribbons, original geometry only in presentation
current={'collection':staging,'root':bpy.data.objects.new('Presentation_ROOT',None),'objects':[]};staging.objects.link(current['root'])
cube('Presentation_Inland_Garden',(0,36,-.25),(150,70,.12),'grass')
cube('Presentation_Extended_Sand',(0,-6,-.32),(150,22,.1),'sand')
foam=mat('Presentation_Shore_Foam',(.75,.85,.77),.85)
for i in range(3):
    vs=[];fs=[]
    for j in range(81):
        x=-32+j*.8;y=-17.5-i*1.5+.2*sin(x*.7+i)
        vs.extend([(x,y,-.14+i*.005),(x,y+.12+(.04*sin(x)),-.14+i*.005)])
    for j in range(80):a=j*2;fs.append((a,a+1,a+3,a+2))
    mesh(f'Presentation_Foam_{i}',vs,fs,foam)
scene=bpy.context.scene;scene.name='Coastal_Preview'
world=bpy.data.worlds.new('Coastal_Afternoon');world.use_nodes=True;scene.world=world
wn=world.node_tree.nodes;wn.clear();sky=wn.new('ShaderNodeTexSky');sky.sky_type='NISHITA';sky.sun_elevation=.6;sky.sun_rotation=2.3;sky.altitude=.2;sky.air_density=1;sky.dust_density=2
bg=wn.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.35;wo=wn.new('ShaderNodeOutputWorld');world.node_tree.links.new(sky.outputs['Color'],bg.inputs['Color']);world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface'])
bpy.ops.object.light_add(type='SUN',location=(0,0,12));sun=bpy.context.object;sun.name='Presentation_Sun';sun.rotation_euler=(.55,-.4,-.7);sun.data.energy=2;sun.data.angle=.08
bpy.ops.object.camera_add(location=(22,-29,18));cam=bpy.context.object;cam.name='Preview_Camera';cam.rotation_euler=(Vector((0,-1,2.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.lens=43;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=96;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-2.0;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Kerala_Coastal_Assets.blend'))
scene.render.filepath=str(OUT/'previews'/'coastal_asset_preview.png')
if '--skip-render' not in sys.argv: bpy.ops.render.render(write_still=True)
print('ENVIRONMENT_BUILD_COMPLETE',str(OUT))
