import bpy
import bmesh
import json
from mathutils import Matrix
from mathutils import Vector
from functools import reduce

d16 = lambda x: x * 16.0

def index(li, ele):
	for i, e in enumerate(li):
		if (e[0] == ele[0] and e[1] == ele[1]):
			return i
	raise Exception("Could not find " + str(ele) + " in " + str(li))

fd = { (0, -1, 0) : 'down',
		(0, 1, 0) : 'up',
		(-1, 0, 0) : 'west',
		(1, 0, 0) : 'east',
		(0, 0, -1) : 'north',
		(0, 0, 1) : 'south' }

fsolver = {(0, 2, 1) : (90, False, True),
			(3, 1, 0) : (0, False, False), #1 
			(2, 0, 3) : (90, False, True), #2 
			(1, 3, 2) : (0, False, False), #3 
			(3, 1, 2) : (90, False, True), #4
			(0, 2, 3) : (0, False, False), #0 ff
			(1, 3, 0) : (90, False, True),
			(2, 0, 1) : (0, False, False) } 

projectionAxis = {  (0, 0, -1) : ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0)),
					(0, 0, 1) : ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
					(1, 0, 0) :  ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
					(-1, 0, 0) :  ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
					(0, -1, 0) :  ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
					(0, 1, 0) :  ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)) }

def project(v, normal):
	p1, p2 = projectionAxis[tuple(normal)]
	p1, p2 = Vector(p1), Vector(p2)
	result = (p1.dot(v), p2.dot(v))
	print("res", result, "normal", tuple(normal))

	return result

def processFace(f):
	global out, uv_layer
	p = {}
	co = sorted(f.verts, key = lambda v: project(v.co.xyz, f.normal.normalized()))	
	#test if current face only got 4 vertices (is a quad)
	if (len(co) != 4):
		raise Exception("Found non-quad face")
	#test end

	#test if a single coord is out of bounds
	allCoords = list(map(lambda v: list(v.co.xyz), f.verts))
	test = list(reduce(lambda x, y: x + y, allCoords))
	for x in test:
		if (x > 2 or x < -1):
			raise Exception("Model out of bounds: " + str(x))
	#test end			
		
	
	face = type('face', (object,), {})()
	face.fro = co[0]
	face.to = co[-1]
	face.nor = f.normal	
	uvl = {} #create uv lookup table containing pairs of bmvert : uv-coord as list
	uli = []
	for loop in f.loops:
		t = list(map(lambda x: round(x, 3), list(loop[uv_layer].uv)))
		uvl[loop.vert] = t
		uli.append(t)	
	xs = list(map(lambda x: x[0], uli))
	ys = list(map(lambda y: y[1], uli))
	t, b, l, r = max(ys), min(ys), min(xs), max(xs)	
	uli = [[l, b], [l, t], [r, t], [r, b]]	#is sorted CW starting from bottom left corner

	uv = list(map(d16, uvl[face.fro] + uvl[face.to]))
	
	froUvIndex = index(uli, uvl[face.fro])
	toUvIndex = index(uli, uvl[face.to])
	testIndex = index(uli, uvl[co[1]])
	fk = sorted(list(fsolver.keys()))
	try:
		print(froUvIndex, toUvIndex, testIndex, ":", fk.index((froUvIndex, toUvIndex, testIndex)))	
	except Exception as e:
		print("from:", face.fro.co.xyz, "to:", face.to.co.xyz)
		raise e

	face.rot, swapx, swapy = fsolver[(froUvIndex, toUvIndex, testIndex)]	
	c0, c1, c2, c3 = 0, 1, 2, 3 #0321
	if (swapx): c0, c2 = 2, 0
	if (swapy): c1, c3 = 3, 1
	face.uv = [uv[c0], 16.0 - uv[c1], uv[c2], 16.0 - uv[c3]]	
	return face

#face[from vert, to vert, normal, uv[0-3]]
def export(faces, path):
	out = {}
	out['ambientocclusion'] = False
	out['textures'] = { 'z00' : 'blocks/z00'}
	out['elements'] = []
	for face in faces:
		p = {}
		p['from'] = list(map(d16, list(face.fro.co.yzx)))
		p['to'] = list(map(d16, list(face.to.co.yzx)))
		p['shade'] = False

		#uv face...
		uvf = {}
		sn = fd[tuple(face.nor.normalized().yzx)] #normal in string form #EDIT THIS XYZ!!!! OR fd
		uvf[sn] = {}
		uvf[sn]['texture'] = '#z00'
		uvf[sn]['cullface'] = True
		uvf[sn]['uv'] = face.uv		
		uvf[sn]['rotation'] = face.rot		
		p['faces'] = uvf
		out['elements'].append(p)	

	fi = open(path, 'w')
	fi.write(json.dumps(out, indent=4, separators=(',', ': ')))
	fi.close()

def main():
	global out, uv_layer
	print("main called")

	me = bpy.context.object.data

	bm = bmesh.new()
	bm.from_mesh(me)
	
	bm.verts.ensure_lookup_table()
	bm.faces.ensure_lookup_table()
	uv_layer = bm.loops.layers.uv.active

	processedFaces = []
	forder = sorted(list(bm.faces), key = lambda f: f.verts[0].co.x)
	for f in forder:
		processedFaces.append(processFace(f))

	#export
	path = 'C:\\Users\\HM\\AppData\\Roaming\\.minecraft\\resourcepacks\\Konv2\\assets\\minecraft\\models\\block\\coal_ore.json'
	export(processedFaces, path)

	bm.free()  # free and prevent further access		

	print("done")
