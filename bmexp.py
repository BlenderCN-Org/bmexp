import bpy
import bmesh
import json
from mathutils import Matrix
from mathutils import Vector
from functools import reduce
from operator import attrgetter

d16 = lambda x: x * 16.0
#d16 = lambda x: x

round4 = lambda x: round(x, 4)
mcos = lambda vec: attrgetter('yzx')(vec)

fd = { (0, -1, 0) : 'down', #in MCOS
		(0, 1, 0) : 'up',
		(-1, 0, 0) : 'west',
		(1, 0, 0) : 'east',
		(0, 0, -1) : 'north',
		(0, 0, 1) : 'south' }	

#vector distance to positive positive positive
#10000 is an arbritary big number which is hopefully big enough
def vecDistToPPP(vec):
	return (vec.co - Vector([10000.0, 10000.0, 10000.0])).length

#vector distance to negative negative
#only used for textures
def vecDistToNN(vec):
	vec = Vector(vec)
	return (vec - Vector([-10000.0, -10000.0])).length


def roundTouple(tu):
	return tuple(map(lambda x: float(int(x)), tu))

def processFace(f):
	global out, uv_layer
	p = {}
	co = f.verts

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

	fro = co[0]
	to = co[0]
	for v in co: #tiny sort since sorted doesn't work shit
		if (vecDistToPPP(v) > vecDistToPPP(fro)):
			fro = v
		if (vecDistToPPP(v) < vecDistToPPP(to)):						
			to = v
			
	face.fro = fro
	face.to = to
	face.nor = fd[roundTouple(mcos(f.normal.normalized()))]	

	#FIND ROTATION
	uvl = {} #create uv lookup table containing pairs of bmvert : uv-coord as list		
	for loop in f.loops:
		uvl[loop.vert] = list(loop[uv_layer].uv)

	

	### MCOS ROTATIONS
	uvl = {} #create uv lookup table containing pairs of bmvert : uv-coord as list	

	#mirror y coordinate of all uv coordinates
	for loop in f.loops:
		uv = loop[uv_layer].uv		
		uv.y = 1.0 - uv.y		
		uvl[loop.vert] = list(uv)	

	#find smallest (upper left)(closest to 0,0)
	#find biggest (lower right)(furthest away to 0,0)
	uvCoords = list(uvl.values())	
	smallestUV = uvCoords[0]
	biggestUV = uvCoords[0]	
	for uvCoord in uvCoords[1:]:
		if (vecDistToNN(smallestUV) > vecDistToNN(uvCoord)):
			smallestUV = uvCoord
		if (vecDistToNN(biggestUV) < vecDistToNN(uvCoord)):
			biggestUV = uvCoord
	print(smallestUV, biggestUV)
	uv = list(map(d16, smallestUV + biggestUV))
	#uv = list(map(d16, uvl[face.fro] + uvl[face.to]))

	face.uv = uv
	face.rotation = -90
	return face

#face[from vert, to vert, normal, uv[0-3]]
#only use mcos here
def export(faces, path):
	out = {}
	out['ambientocclusion'] = False
	out['textures'] = { 'z00' : 'blocks/z00'}
	out['elements'] = []
	for face in faces:
		p = {}
		p['from'] = list(map(round4, list(map(d16, list(mcos(face.fro.co))))))
		p['to'] = list(map(round4, list(map(d16, list(mcos(face.to.co))))))
		p['shade'] = False

		#uv face...
		uvf = {}
		sn = face.nor #normal in string form eg. 'UP'
		uvf[sn] = {}
		uvf[sn]['texture'] = '#z00'
		uvf[sn]['cullface'] = True
		uvf[sn]['uv'] = face.uv
		uvf[sn]['rotation'] = face.rotation % 360

		p['faces'] = uvf
		out['elements'].append(p)


	fi = open(path, 'w')
	fi.write(json.dumps(out, indent=4, separators=(',', ': ')))
	fi.close()

def main():
	global out, uv_layer
	print("[BmExp] Exporting!")

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

	print("[BmExp] done!")