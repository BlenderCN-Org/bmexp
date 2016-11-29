import bpy
import bmesh
import json
from mathutils import Matrix
from mathutils import Vector
from functools import reduce

d16 = lambda x: x * 16.0
m = Matrix([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]) #swap y and z
fd = { (0, -1, 0) : 'down',
		(0, 1, 0) : 'up',
		(-1, 0, 0) : 'west',
		(1, 0, 0) : 'east',
		(0, 0, -1) : 'north',
		(0, 0, 1) : 'south' }

def roundTouple(tu):
	return tuple(map(lambda x: float(int(x)), tu))

def processFace(f):
	global out, uv_layer
	p = {}
	co = sorted(f.verts, key = lambda v: tuple(v.co.xyz))	
	#test if current face only got 4 vertices (is a quad)
	if (len(co) != 4):
		raise Exception("Found non-quad face")
	#test end

	#test if a single coord is out of bounds
	allCoords = list(map(lambda v: list(v.co.xyz), f.verts))
	test = list(reduce(lambda x, y: x + y, allCoords))
	for x in test:
		if (x > 2 or x < -1):
			raise Exception("Model out of bounds")
	#test end			
		
	
	face = type('face', (object,), {})()
	face.fro = co[0]
	face.to = co[-1]
	face.nor = f.normal	
	uvl = {} #create uv lookup table containing pairs of bmvert : uv-coord as list	
	for loop in f.loops:
		uvl[loop.vert] = list(loop[uv_layer].uv)	
	uv = list(map(d16, uvl[face.fro] + uvl[face.to]))
	face.uv = [uv[0], 16.0 - uv[1], uv[2], 16.0 - uv[3]]	
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
		sn = fd[roundTouple(face.nor.normalized().yzx)] #normal in string form #EDIT THIS XYZ!!!! OR fd
		print("sn", sn)
		uvf[sn] = {}
		uvf[sn]['texture'] = '#z00'
		uvf[sn]['cullface'] = True
		uvf[sn]['uv'] = face.uv

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
	for f in bm.faces:
		processedFaces.append(processFace(f))

	#export
	path = 'C:\\Users\\HM\\AppData\\Roaming\\.minecraft\\resourcepacks\\Konv2\\assets\\minecraft\\models\\block\\coal_ore.json'
	export(processedFaces, path)

	bm.free()  # free and prevent further access		

	print("done")