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
	global out
	p = {}
	co = sorted(list(map(lambda v: list(v.co.xyz), f.verts)))

	#test if a single coord is out of bounds
	test = list(reduce(lambda x, y: x + y, co))
	for x in test:
		if (x > 2 or x < -1):
			raise Exception("Model out of bounds")

	p['from'] = list(map(d16, co[0]))
	p['to'] = list(map(d16, co[-1]))
	p['shade'] = False
	mf = {}
	sn = fd[tuple(f.normal.normalized().xyz)] #string normal
	print("sn", sn)
	mf[sn] = {} #minecraft face
	mf[sn]['uv'] = [0.0, 0.0, 1.0, 1.0]
	mf[sn]['texture'] = '#z00'
	mf[sn]['cullface'] = True
	p['faces'] = mf
	out['elements'].append(p)

def main():
	global out
	print("main called")

	me = bpy.context.object.data

	bm = bmesh.new()
	bm.from_mesh(me)
	bm.verts.ensure_lookup_table()
	m = Matrix([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]) #swap y and z
	for v in bm.verts:
		v.co = m * v.co

	bm.faces.ensure_lookup_table()
	out = {}
	out['ambientocclusion'] = False
	out['textures'] = { 'z00' : 'blocks/z00'}
	out['elements'] = []

	for f in bm.faces:
		f.normal_update()
		procFace(f)

	bm.free()  # free and prevent further access
	print(json.dumps(out, indent=4, separators=(',', ': ')))
	fi = open('/home/stxxt/.minecraft/resourcepacks/ATaleOfKreios/assets/minecraft/models/block/coal_ore.json', 'w')
	fi.write(json.dumps(out, indent=4, separators=(',', ': ')))
	fi.close()

	print("done")