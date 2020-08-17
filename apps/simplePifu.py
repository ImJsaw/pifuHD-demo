from PIL import Image
import sys
import os
import glob
from .recon import reconWrapper
import argparse
import trimesh
###############################################################################################
##                   Setting
###############################################################################################
parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input_path', type=str, default='./simple_pifu')
parser.add_argument('-o', '--out_path', type=str, default='./')
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

#get all image in folder & gen txt
for imgs in glob.glob(args.input_path+"/*.jpg"):
	autoTxt(imgs)
for imgs in glob.glob(args.input_path+"/*.png"):
	autoTxt(imgs)

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

