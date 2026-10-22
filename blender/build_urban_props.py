"""Original Kerala-inspired low-poly urban kit; no downloaded geometry or textures.
Run: blender -b --factory-startup -t 4 --python blender/build_urban_props.py
Axes: Blender X frontage, Y depth, Z up; front -Y; ground-centred origin.
Each GLB is Y-up, merged into at most five material meshes. Fictional district.
"""
import bpy, bmesh, math, json, shutil, struct, hashlib, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/infrastructure/urban'; WEB=ROOT/'assets/web'; PUB=ROOT/'web/public/assets'
for p in (OUT,OUT/'native',OUT/'previews',WEB,PUB):p.mkdir(parents=True,exist_ok=True)
SC=bpy.context.scene
bpy.context.preferences.filepaths.save_version=0
SC.unit_settings.system='METRIC'; SC.unit_settings.scale_length=1
BUFFERS={}; MATS=[]

def reset():
    global BUFFERS,MATS
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):bpy.data.collections.remove(collection)
    for datablocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials):
        for d in list(datablocks):
            if not d.users:datablocks.remove(d)
    BUFFERS={i:[[],[]] for i in range(5)}
    MATS=[]
    for i,(n,c,r,mt) in enumerate([
        ('Warm_Lime_Plaster',(.73,.69,.54),.85,0),
        ('Deep_Window_Glass',(.025,.068,.075),.28,.18),
        ('Kerala_Teal_Trim',(.025,.32,.30),.66,0),
        ('Terracotta_Roof',(.45,.14,.065),.9,0),
        ('Stone_And_Metal',(.24,.27,.245),.84,.04)]):
        m=bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*c,1)
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1)
        p.inputs['Roughness'].default_value=r;p.inputs['Metallic'].default_value=mt
        m.use_backface_culling=False;MATS.append(m)

def mesh(v,f,m):
    vs,fs=BUFFERS[m]; off=len(vs);vs.extend(v);fs.extend(tuple(off+k for k in face) for face in f)

def box(x,y,z,w,d,h,m=0):
    a,b,c=w/2,d/2,h/2
    vs=[(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
        (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
    mesh(vs,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],m)

def quad(a,b,c,d,m=1):mesh([a,b,c,d],[(0,1,2,3)],m)

def tube(a,b,r,m=4,n=6):
    a,b=Vector(a),Vector(b);v=b-a
    if v.length<1e-5:return
    v.normalize();u=v.cross(Vector((0,0,1)))
    if u.length<.01:u=v.cross(Vector((0,1,0)))
    u.normalize();w=v.cross(u).normalized()
    pts=[tuple(p+r*(u*math.cos(2*math.pi*i/n)+w*math.sin(2*math.pi*i/n))) for p in (a,b) for i in range(n)]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh(pts,faces,m)

def hiproof(x,y,z,w,d,h,m=3):
    # Rectangular eave at z, compact hipped ridge along frontage.
    vs=[(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z),
        (x-w*.30,y,z+h),(x+w*.30,y,z+h)]
    mesh(vs,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(0,3,2,1)],m)

def front_window(x,y,z,w,h,balcony=False):
    # Nested planes create crisp frames without spending boxes on every window.
    quad((x-w/2-.10,y-.02,z-h/2-.10),(x+w/2+.10,y-.02,z-h/2-.10),(x+w/2+.10,y-.02,z+h/2+.10),(x-w/2-.10,y-.02,z+h/2+.10),2)
    quad((x-w/2,y-.031,z-h/2),(x+w/2,y-.031,z-h/2),(x+w/2,y-.031,z+h/2),(x-w/2,y-.031,z+h/2),1)
    quad((x-.027,y-.045,z-h/2),(x+.027,y-.045,z-h/2),(x+.027,y-.045,z+h/2),(x-.027,y-.045,z+h/2),0)
    quad((x-w/2,y-.045,z-.022),(x+w/2,y-.045,z-.022),(x+w/2,y-.045,z+.022),(x-w/2,y-.045,z+.022),0)
    if balcony:
        box(x,y-.40,z-h*.48,w+.5,.85,.12,0)
        box(x,y-.79,z-.14,w+.5,.10,.64,2)
        box(x,y-.85,z+.20,w+.55,.09,.07,0)

def side_window(x,y,z,w,h):
    s=1 if x>0 else -1
    a=x+s*.080;b=x+s*.086;c=x+s*.091
    quad((a,y-w/2-.08,z-h/2-.08),(a,y+w/2+.08,z-h/2-.08),(a,y+w/2+.08,z+h/2+.08),(a,y-w/2-.08,z+h/2+.08),2)
    quad((b,y-w/2,z-h/2),(b,y+w/2,z-h/2),(b,y+w/2,z+h/2),(b,y-w/2,z+h/2),1)
    quad((c,y-.023,z-h/2),(c,y+.023,z-h/2),(c,y+.023,z+h/2),(c,y-.023,z+h/2),0)

def text(label,x,y,z,size,m=0):
    curve=bpy.data.curves.new('Procedural_Sign','FONT');curve.body=label;curve.size=size
    curve.align_x='CENTER';curve.align_y='CENTER';curve.extrude=0;curve.resolution_u=1
    ob=bpy.data.objects.new('Original_Generic_Sign',curve);SC.collection.objects.link(ob)
    ob.location=(x,y,z);ob.rotation_euler=(math.pi/2,0,0)
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(deps);me=ev.to_mesh()
    mesh([tuple(ob.matrix_world@v.co) for v in me.vertices],[tuple(p.vertices) for p in me.polygons],m)
    ev.to_mesh_clear();bpy.data.objects.remove(ob,do_unlink=True)

def watertank(x,y,z,r=.65,h=1.0):
    tube((x,y,z),(x,y,z+h),r,4,8)
    tube((x,y,z+h),(x,y,z+h+.08),r*.90,1,8)
    box(x,y,z-.12,r*2+.18,r*2+.18,.24,0)

def shutter(x,y,z,w,h):
    box(x,y+.025,z,w,.06,h,4)
    for k in range(7):box(x,y-.015,z-h*.43+k*h*.14,w,.025,.025,0)
    box(x,y-.03,z-h*.37,.10,.03,.12,1)

def shoprow_a():
    # Entire envelope 12 x 10 x 10; front street face -Y.
    box(0,.40,4.35,12,9.2,8.7,0)
    box(0,.40,.15,12,9.2,.3,4)
    for z in (3.10,5.85,8.62):box(0,.35,z,12,9.3,.18,2)
    for x in (-4,0,4):
        shutter(x,-4.235,1.40,3.15,2.40)
        box(x,-4.27,2.80,3.50,.13,.48,2)
        for z in (4.45,7.12):front_window(x,-4.24,z,2.65,1.75,True)
        # Two-tone sloping fabric canopy, ending exactly at -5.
        for k in range(4):
            xa=x-1.80+k*.9;xb=xa+.9
            quad((xa,-4.25,2.56),(xb,-4.25,2.56),(xb,-5,2.32),(xa,-5,2.32),2 if k%2==0 else 0)
            box((xa+xb)/2,-4.97,2.25,.90,.055,.14,2 if k%2==0 else 0)
    for x,label in ((-4,'BAKERY'),(0,'STORES'),(4,'TEA')):text(label,x,-4.348,2.80,.31)
    for x in (-5.94,5.94):
        for y in (-1.5,2.0):
            for z in (4.45,7.12):side_window(x,y,z,1.65,1.75)
    # Roof terrace, capped stair tower and tank (highest z = 10).
    box(0,.4,8.88,11.8,9.0,.36,0)
    box(-4.6,2.6,9.2,2.25,3.0,.65,2);hiproof(-4.6,2.6,9.525,2.5,3.2,.475)
    watertank(4.5,2.5,8.92,.62,1.0)
    for x in (-5.4,5.4):box(x,.1,8.99,.12,7.7,.28,2)
    for y in (-3.7,3.9):box(0,y,8.99,10.8,.12,.28,2)

def shoprow_b():
    # Low mixed frontage with genuine pitched roof silhouette.
    MATS[0].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.69,.51,.26,1)
    MATS[0].diffuse_color=(.69,.51,.26,1)
    box(0,.35,2.9,10,8.3,5.8,0);box(0,.35,.13,10,8.3,.26,4)
    hiproof(0,.2,5.8,10,8.6,1.2)
    box(0,-3.84,2.95,9.9,.15,.25,2)
    for x,label in ((-2.5,'MARKET'),(2.5,'COAST MART')):
        shutter(x,-3.84,1.30,3.7,2.30)
        box(x,-3.9,2.64,4.35,.12,.49,2);text(label,x,-3.97,2.64,.32)
        for xx in (x-.95,x+.95):front_window(xx,-3.85,4.35,1.25,1.65)
        # Broad roof overhang / front entrance canopy.
        quad((x-2.35,-3.85,2.35),(x+2.35,-3.85,2.35),(x+2.35,-4.5,2.12),(x-2.35,-4.5,2.12),3)
    for x in (-4.94,4.94):
        for y in (-1.2,1.5):side_window(x,y,4.35,1.3,1.65)
    # Roof tile-course ridge strips are geometry, not textures.
    for y in (-3,-1.5,0,1.5,3):
        z=5.8+1.2*(1-abs(y-.2)/4.3)
        box(0,y,z+.015,2*(3+2*abs(y-.2)/4.3)-.15,.05,.04,3)

def apartment():
    box(0,.5,11.65,16,13,23.3,0);box(0,.5,.18,16,13,.36,4)
    # Teal vertical inset and white-edged storey bands give layered facade depth.
    box(0,-6.04,11.7,2.2,.16,22.8,2)
    for floor in range(8):
        z=1.6+floor*2.78
        box(0,.50,z+1.27,15.9,12.95,.13,0)
        for x in (-5.9,-2.7,2.7,5.9):front_window(x,-6.065,z,2.05,1.65,True)
        # Rear window grid and side elevations, no invisible orphan rear wall.
        for x in (-5.8,-2.0,2.0,5.8):
            quad((x-1,7.016,z-.8),(x+1,7.016,z-.8),(x+1,7.016,z+.8),(x-1,7.016,z+.8),1)
        for side in (-1,1):
            for y in (-3.3,.25,3.8):side_window(side*7.94,y,z,1.65,1.65)
    # Front ground-floor lobby and columns.
    box(0,-6.10,.95,1.6,.18,1.9,1)
    for x in (-.95,.95):box(x,-6.35,1.1,.16,.45,2.2,0)
    box(0,-6.45,2.21,2.3,.65,.16,2)
    box(0,.5,23.5,15.8,12.8,.4,0)
    hiproof(-4.3,.6,23.70,6.7,10.8,1.3)
    hiproof(4.3,.6,23.70,6.7,10.8,1.3)
    box(0,3.3,24.12,2.2,3.0,.83,2)
    watertank(0,-1.3,23.7,.65,1.0)

def office():
    box(0,.4,8.3,22,15.2,16.6,0)
    box(0,.4,.18,22,15.2,.36,4)
    # Bands of dark curtain wall, broken by cream piers and teal sunshades.
    for row in range(5):
        z=1.7+row*3.0
        for col in range(8):
            x=-9.2+col*2.63
            quad((x-1.05,-7.215,z-1.0),(x+1.05,-7.215,z-1.0),(x+1.05,-7.215,z+1.0),(x-1.05,-7.215,z+1.0),1)
            box(x,-7.25,z,.055,.07,2.0,2)
        box(0,-7.45,z+1.12,21.7,.55,.13,2)
        for side in (-1,1):
            for y in (-5,-1.8,1.4,4.6):side_window(side*10.94,y,z,2.25,2.05)
        for x in (-8,-4,0,4,8):
            quad((x-1.4,8.015,z-1),(x+1.4,8.015,z-1),(x+1.4,8.015,z+1),(x-1.4,8.015,z+1),1)
    # Shaded ground entrance and roof parapet.
    box(0,-7.5,3.0,7.1,1.0,.20,2)
    for x in (-3.3,3.3):box(x,-7.5,1.5,.25,.40,3.0,0)
    box(0,-7.24,1.3,3.5,.11,2.6,1)
    box(0,-7.94,2.66,6.5,.10,.46,2)
    text('COAST HOUSE',0,-8.002,2.66,.38,0)
    box(0,.4,16.85,21.8,15,.5,2)
    box(-5,3.0,17.4,6,5,1.2,0)
    box(5,3.0,17.3,5,4,1.0,4)
    for i in range(5):box(3.2+i*.9,3.0,17.84,.6,3.2,.08,1)

def teastall():
    box(0,.35,.12,3.6,2.3,.24,4)
    box(0,.72,1.25,3.5,1.3,2.26,0)
    box(0,-.06,1.38,2.9,.04,1.02,1)
    box(0,-.36,.77,3.3,.65,1.18,2)
    box(0,-.38,1.40,3.5,.76,.10,0)
    for x in (-1.75,1.75):box(x,-1.25,1.35,.1,.1,2.7,4)
    hiproof(0,0,2.68,4,3,.52)
    box(0,-1.32,2.42,3.65,.10,.46,2);text('TEA & SNACKS',0,-1.38,2.42,.29)
    # Kettle and cups, simple opaque ceramics/metal, within silhouette.
    tube((.8,-.47,1.46),(.8,-.47,1.78),.16,4,8)
    tube((.8,-.47,1.78),(.8,-.47,1.83),.10,4,8)
    tube((.90,-.47,1.68),(1.14,-.47,1.78),.045,4,6)
    for x in (-.6,-.3,0):tube((x,-.55,1.46),(x,-.55,1.60),.06,0,6)
    for x in (-1.05,1.05):
        box(x,-1.06,.44,.5,.45,.09,3)
        for xx in (x-.18,x+.18):box(xx,-1.06,.22,.055,.32,.4,4)

def fishingnet():
    # Stylized working cantilever. Rear land platform + A-frame, forward boom/net.
    # Envelope exact 14 x 18 x 12, base footprint ground-centred.
    MATS[3].node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.23,.10,.038,1)
    MATS[3].diffuse_color=(.23,.10,.038,1)
    box(0,5.6,.32,5.6,6.8,.36,3)
    for x in (-2.45,2.45):
        for y in (2.55,8.65):tube((x,y,0),(x,y,2.25),.14,3,6)
    for x in (-2.4,2.4):
        tube((x,3.2,.5),(0,5.5,11.84),.16,3,6)
        tube((x,8.3,.5),(0,5.5,11.84),.16,3,6)
    tube((0,5.5,11.84),(0,5.5,12),.035,3,4)
    # Long pivoted cantilever and cross arm sit over the suspended net.
    tube((0,8.75,3.8),(0,-3.7,9.3),.22,3,8)
    tube((-6.84,-4.5,7.0),(6.84,-4.5,7.0),.16,3,6)
    for s in (-1,1):
        tube((0,-3.6,9.26),(s*6.84,-4.5,7.0),.11,3,6)
        tube((0,5.5,11.82),(s*6.6,-4.5,7.02),.026,4,4)
        tube((0,5.5,11.82),(s*2.4,8.3,.6),.028,4,4)
    # Net corners and edge lines. Lowest central sag above ground; grid ribbons.
    corners=[(-7,-9,2.25),(7,-9,2.25),(7,-.6,3.0),(-7,-.6,3.0)]
    for p in corners:
        top=(-6.80 if p[0]<0 else 6.80,-4.5,7)
        tube(top,p,.025,4,4)
    def np(u,v):
        x=-7+14*u;y=-9+8.4*v
        z=2.25+.75*v-1.35*math.sin(math.pi*u)*math.sin(math.pi*v)
        return Vector((x,y,z))
    # Narrow ribbons make a genuinely open net, no large opaque sheet.
    def ribbon(a,b,width=.022):
        a,b=Vector(a),Vector(b);v=b-a;side=Vector((-v.y,v.x,0)).normalized()*width
        quad(tuple(a-side),tuple(b-side),tuple(b+side),tuple(a+side),4)
    for u in [i/12 for i in range(13)]:
        for j in range(8):ribbon(np(u,j/8),np(u,(j+1)/8))
    for v in [i/8 for i in range(9)]:
        for j in range(12):ribbon(np(j/12,v),np((j+1)/12,v))
    # Hanging stone counterweights are a defining functional detail.
    for j,x in enumerate((-.75,-.25,.25,.75)):
        top=(x,8.5,4.1);bottom=(x,8.5,1.25+j*.38)
        tube(top,bottom,.025,4,4)
        box(x,8.5,bottom[2],.34,.34,.42,4)
    # Thin timber boardwalk pieces; total Y=18 from net front to platform back.
    box(0,8.86,.34,5.6,.28,.34,3)

BUILDERS=[('KeralaShopRow_A',shoprow_a,(12,10,10)),('KeralaShopRow_B',shoprow_b,(10,9,7)),
 ('KeralaApartment_A',apartment,(16,14,25)),('KeralaOffice_A',office,(22,16,18)),
 ('KeralaTeaStall',teastall,(4,3,3.2)),('ChineseFishingNet',fishingnet,(14,18,12))]
REPORT={
 'version':'urban-kit-v8-1','source':'blender/build_urban_props.py',
 'provenance':'Original procedural Blender geometry. No external models, photos, image textures, trademarks or logos bundled.',
 'reference_note':'Reference silhouettes only: official Kerala Tourism, KMRL and Kochi Water Metro. Fictional Kerala-inspired district, not accurate Kappil geography.',
 'reference_urls':['https://kochimetro.org/completed-projects/','https://www.keralatourism.org/kochi/backwaters-kochi.php','https://www.keralatourism.org/kochi/chinese-fishing-nets-kochi'],
 'axes_blender':{'front':'-Y','up':'+Z','frontage':'+X'},
 'axes_gltf':{'front':'+Z','up':'+Y','frontage':'+X'},
 'origin':'Ground-centre of planned footprint. No parent transforms; metre scale.',
 'collision_note':'Visual meshes only; caller should use separate simplified building AABBs. Fishing net is waterfront scenery, not a drive-through mesh.',
 'assets':[]}

def export_asset(name,planned):
    collection=bpy.data.collections.new(name);SC.collection.children.link(collection)
    root=bpy.data.objects.new(name,None);collection.objects.link(root)
    root['original_asset']=True;root['fictional_kerala_inspired']=True
    root['front_blender']='-Y';root['up_blender']='+Z';root['origin']='ground-centre';root['units']='metres'
    objects=[]
    for i,(vs,fs) in BUFFERS.items():
        if not vs:continue
        me=bpy.data.meshes.new(name+'_'+MATS[i].name);me.from_pydata(vs,[],fs);me.update()
        bm=bmesh.new();bm.from_mesh(me)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_area()<1e-8],context='FACES')
        bm.normal_update();bm.to_mesh(me);bm.free();me.update()
        ob=bpy.data.objects.new(name+'_'+MATS[i].name,me);collection.objects.link(ob);ob.data.materials.append(MATS[i]);ob.parent=root;objects.append(ob)
    bpy.context.view_layer.update()
    # Small, explicit normalization to the declared envelope guarantees pivot and extents.
    # This corrects trim/ribbon thickness only; no arbitrary runtime rescaling is required.
    verts=[v.co for ob in objects for v in ob.data.vertices]
    low=[min(v[i] for v in verts) for i in range(3)];high=[max(v[i] for v in verts) for i in range(3)]
    raw_size=[high[i]-low[i] for i in range(3)]
    for ob in objects:
        for v in ob.data.vertices:
            v.co.x=(v.co.x-(low[0]+high[0])/2)*planned[0]/raw_size[0]
            v.co.y=(v.co.y-(low[1]+high[1])/2)*planned[1]/raw_size[1]
            v.co.z=(v.co.z-low[2])*planned[2]/raw_size[2]
        ob.data.update()
        # Filter again after Float32 envelope normalization: text tessellation can
        # collapse extremely thin glyph-edge slivers only after coordinate rounding.
        bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_area()<1e-6],context='FACES')
        bm.normal_update();bm.to_mesh(ob.data);bm.free();ob.data.update()
    bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
    for ob in objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=root
    path=WEB/(name+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_extras=True,export_animations=False)
    shutil.copy2(path,PUB/path.name)
    SC['reference_geometry']='Fictional Kerala-inspired urban kit, original procedural geometry'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'native'/(name+'.blend')))
    data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length])
    tris=sum(doc['accessors'][p['indices']]['count']//3 for me in doc['meshes'] for p in me['primitives'])
    draws=sum(len(m['primitives']) for m in doc['meshes'])
    limit=2000 if name=='ChineseFishingNet' else 3000
    # glTF bounds are metre-space POSITION bounds after axis conversion.
    aabbs=[doc['accessors'][p['attributes']['POSITION']] for me in doc['meshes'] for p in me['primitives']]
    lo=[min(a['min'][i] for a in aabbs) for i in range(3)];hi=[max(a['max'][i] for a in aabbs) for i in range(3)]
    qa={'triangles_within_budget':tris<=limit,'materials_at_most_5':len(doc['materials'])<=5,'draws_at_most_5':draws<=5,
        'no_image_textures':not doc.get('images'),'positive_y_up_height':abs(lo[1])<1e-4,'finite_positions':all(math.isfinite(c) for a in aabbs for c in a['min']+a['max'])}
    item={'name':name,'native_collection':name,'root_object':name,'file':'assets/web/'+path.name,'native':'assets/infrastructure/urban/native/'+name+'.blend',
          'preview':'assets/infrastructure/urban/previews/'+name+'.png','triangles':tris,'triangle_budget':limit,'draw_primitives':draws,'materials':len(doc['materials']),
          'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'dimensions_blender_xyz_m':list(planned),'bounds_blender':{'min':[-planned[0]/2,-planned[1]/2,0],'max':[planned[0]/2,planned[1]/2,planned[2]]},
          'bounds_gltf_xyz_m':{'min':lo,'max':hi},'raw_dimensions_before_envelope_normalization':raw_size,'qa':qa}
    REPORT['assets'].append(item)
    print('URBAN_EXPORTED',name,json.dumps(item),flush=True)
    if not all(qa.values()):raise RuntimeError(name+' QA failed '+str(qa))
    return objects

def preview(name,planned):
    world=bpy.data.worlds.new('Urban_Preview_World');world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs[0].default_value=(.22,.32,.36,1)
    world.node_tree.nodes.get('Background').inputs[1].default_value=.55;SC.world=world
    g=bpy.data.materials.new('Preview_Only_Ground');g.use_nodes=True
    g.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.16,.19,.16,1)
    g.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
    bpy.ops.mesh.primitive_plane_add(size=max(planned)*12,location=(0,0,-.015));bpy.context.object.data.materials.append(g)
    bpy.ops.object.light_add(type='SUN',location=(-10,-15,25));bpy.context.object.data.energy=2.1
    bpy.context.object.rotation_euler=(math.radians(25),math.radians(-25),math.radians(-25));bpy.context.object.data.angle=.13
    bpy.ops.object.light_add(type='AREA',location=(0,-planned[1],planned[2]*1.5+4));bpy.context.object.data.energy=600;bpy.context.object.data.size=max(planned)*1.2
    aim=Vector((0,0,planned[2]*.46));span=max(planned[0],planned[1],planned[2])
    bpy.ops.object.camera_add(location=aim+Vector((span*.95,-span*1.5,span*.75)))
    cam=bpy.context.object;cam.rotation_euler=(aim-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=span*1.6;SC.camera=cam
    SC.render.engine='CYCLES';SC.cycles.device='CPU';SC.cycles.samples=16;SC.cycles.use_denoising=False
    SC.render.threads_mode='FIXED';SC.render.threads=4
    SC.render.resolution_x=880;SC.render.resolution_y=720;SC.render.resolution_percentage=100
    SC.view_settings.view_transform='AgX';SC.render.image_settings.file_format='PNG'
    SC.render.filepath=str(OUT/'previews'/(name+'.png'));bpy.ops.render.render(write_still=True)

for name,builder,dimensions in BUILDERS:
    reset();builder();export_asset(name,dimensions);preview(name,dimensions)
REPORT['all_numeric_qa_passed']=all(all(a['qa'].values()) for a in REPORT['assets'])
(OUT/'urban_assets_manifest.json').write_text(json.dumps(REPORT,indent=2)+'\n')
for d in (WEB,PUB):shutil.copy2(OUT/'urban_assets_manifest.json',d/'urban_assets_manifest.json')
print('URBAN_KIT_COMPLETE',json.dumps({'assets':len(REPORT['assets']),'all_qa':REPORT['all_numeric_qa_passed']}),flush=True)
