from PIL import Image
import sys
import os
import glob
from .recon import reconWrapper
import argparse
import trimesh
import math
import cv2
import numpy as np
###############################################################################################
##                   Setting
###############################################################################################
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input_path', type=str, default='./simple_pifu')
parser.add_argument('-o', '--out_path', type=str, default='./simple_pifu')
parser.add_argument('-c', '--ckpt_path', type=str, default='./checkpoints/pifuhd.pt')
parser.add_argument('-r', '--resolution', type=int, default=512)
parser.add_argument('--use_rect', action='store_true', help='use rectangle for cropping')
args = parser.parse_args()
###############################################################################################
##                   Upper PIFu
###############################################################################################

## auto generate rect txt

def autoTxt(path):
	im = Image.open(path)
	w, h = im.size
	imgName = os.path.basename(path)
	txtName = path.rpartition('.')[0]+'_rect.txt'
	txt = open(txtName, "w")
	txt.write("0 0 "+str(w)+" "+str(h))
	txt.close()
	return
##clean mesh
def meshcleaning(file_dir):
    files = sorted([f for f in os.listdir(file_dir) if '.obj' in f])
    for i, file in enumerate(files):
        obj_path = os.path.join(file_dir, file)
        print(f"Processing: {obj_path}")
        mesh = trimesh.load(obj_path)
        cc = mesh.split(only_watertight=False)
        out_mesh = cc[0]
        bbox = out_mesh.bounds
        height = bbox[1,0] - bbox[0,0]
        for c in cc:
            bbox = c.bounds
            if height < bbox[1,0] - bbox[0,0]:
                height = bbox[1,0] - bbox[0,0]
                out_mesh = c
        out_mesh.export(obj_path)

def normalDir(normal):
		return math.copysign(1, normal[2]-0.5)

## generate obj UV
def genUV(texPath):
	UV_obj = texPath.rpartition('.')[0]+'_UV.obj'
	ori_obj = texPath.rpartition('.')[0]+'_pifu.obj'
	
	vertice = []
	uv = []
	normal = []
	face = []
	# Strips the newline character
	Lines = open(ori_obj, 'r').readlines()
	for line in Lines:
		contents = line.split()
		if contents[0] == 'v':
			vertice.append([float(contents[1]), float(
				contents[2]), float(contents[3])])
			uv.append([float(contents[1])*0.5+0.5, float(contents[2])*0.5+0.5])
			normal.append([float(contents[4]), float(
				contents[5]), float(contents[6])])
		elif contents[0] == 'f':
			face.append([float(contents[1]), float(
				contents[2]), float(contents[3])])
	# Write Obj
	outF = open(UV_obj, "w")
	outF.write('mtllib sample.mtl\n')
	outF.write('usemtl Material\n')
	outF.write('s off\n')

	for vertex in vertice:
		outF.write("v {0} {1} {2}\n".format(vertex[0], vertex[1], vertex[2]))

	for index,coord in enumerate(uv):
		if(normalDir(normal[index])==1):
			outF.write("vt {0} {1}\n".format(coord[0]/2.0, coord[1]))
		else:
			outF.write("vt {0} {1}\n".format(coord[0]/2.0+0.5, coord[1]))

	for n in normal:
		outF.write("vn {0} {1} {2}\n".format(n[0], n[1], n[2]))

	for f in face:
		f[0]=int(f[0])
		f[1]=int(f[1])
		f[2]=int(f[2])    
		if(normalDir(normal[f[0]-1])==normalDir(normal[f[1]-1]) 
		and normalDir(normal[f[1]-1])==normalDir(normal[f[2]-1])
		and normalDir(normal[f[0]-1])==normalDir(normal[f[2]-1])
		):
			outF.write("f {0}/{0} {1}/{1} {2}/{2}\n".format(int(f[0]), int(f[1]), int(f[2])))
		else:
			outF.write("f {0} {1} {2}\n".format(int(f[0]), int(f[1]), int(f[2])))
	outF.close()
	# Write texture
	sampleTexture = texPath.rpartition('.')[0]+'_tex.png'
	texture = cv2.imread(texPath)
	texture_gray = cv2.cvtColor(texture,cv2.COLOR_BGR2GRAY)
	texture_gray = cv2.cvtColor(texture_gray,cv2.COLOR_GRAY2BGR)
	vis = np.concatenate((texture, texture_gray), axis=1)
	cv2.imwrite(sampleTexture, vis)
	return
	
# make sure not to get pifu output to TODO
def checkPath(path):
	fileName = os.path.basename(path)
	if fileName[-9:-4] == '_pifu':
		return
	if fileName[-8:-4] == '_tex':
		return
	todoPath.append(path)
	
#get all TODO img
todoPath = []
for img in glob.glob(args.input_path+"/*.jpg"):
	checkPath(img)
for img in glob.glob(args.input_path+"/*.png"):
	checkPath(img)
	
# generate txt
for todo in todoPath:
	autoTxt(todo)

#call pifu
resolution = str(args.resolution)
start_id = -1
end_id = -1
cmd = ['--dataroot', args.input_path, '--results_path', args.out_path,\
       '--loadSize', '1024', '--resolution', resolution, '--load_netMR_checkpoint_path', \
       args.ckpt_path,\
       '--start_id', '%d' % start_id, '--end_id', '%d' % end_id]
reconWrapper(cmd, True)

#clean mesh
meshcleaning(args.out_path)

#generate UV
for todo in todoPath:
	genUV(todo)

