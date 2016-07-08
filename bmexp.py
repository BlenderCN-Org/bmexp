import bpy
import bmesh
import json
from mathutils import Matrix
from functools import reduce

d16 = lambda x: x*16.0

fd = { (0, -1, 0) : 'down',
		(0, 1, 0) : 'up',
		(-1, 0, 0) : 'west',
		(1, 0, 0) : 'east',
		(0, 0, -1) : 'north',
		(0, 0, 1) : 'south' }


def procFace(f):
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

	p['from'] = list(map(d16, list(co[0].co.xyz)))
	p['to'] = list(map(d16, list(co[-1].co.xyz)))
	p['shade'] = False
	mf = {}
	sn = fd[tuple((f.normal.normalized()).xyz)] #string normal
	print("sn", sn)
	mf[sn] = {} #minecraft face
	uvl = {} #create uv lookup table containing pairs of bmvert : uv-coord as list
	for loop in f.loops:
		uvl[loop.vert] = list(loop[uv_layer].uv)
	mf[sn]['uv'] = list(map(d16, uvl[co[0]] + uvl[co[-1]]))
	mf[sn]['texture'] = '#z00'
	mf[sn]['cullface'] = True
	p['faces'] = mf
	out['elements'].append(p)

def main():
	global out, uv_layer
	print("main called")

	me = bpy.context.object.data

	bm = bmesh.new()
	bm.from_mesh(me)

	m = Matrix([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]) #swap y and z
	bm.verts.ensure_lookup_table()
	for v in bm.verts:
		v.co = m * v.co

	bm.faces.ensure_lookup_table()
	for f in bm.faces:
		f.normal = m * f.normal
	uv_layer = bm.loops.layers.uv.active
	out = {}
	out['ambientocclusion'] = False
	out['textures'] = { 'z00' : 'blocks/z00'}
	out['elements'] = []

	for f in bm.faces:
		procFace(f)

	bm.free()  # free and prevent further access
	#print(json.dumps(out, indent=4, separators=(',', ': ')))
	fi = open('/home/stxxt/.minecraft/resourcepacks/ATaleOfKreios/assets/minecraft/models/block/coal_ore.json', 'w')
	fi.write(json.dumps(out, indent=4, separators=(',', ': ')))
	fi.close()

	print("done")
