#
# from __future__ import absolute_import, division, print_function
# from __future__ import absolute_import
# from __future__ import division
# from __future__ import print_function
# import glob
# from paddle import fluid
# from ppdet.core.workspace import load_config, merge_config, create
# from ppdet.utils.eval_utils import parse_fetches
# from ppdet.utils.check import check_gpu, check_version, check_config
# import ppdet.utils.checkpoint as checkpoint
# from ppdet.data.reader import create_reader
#
#
# import os
# import numpy as np
#
# '''Change this 2 lines in every object detection'''
# config_file = "configs/dcn/cascade_rcnn_cls_aware_r200_vd_fpn_dcnv2_nonlocal_softnms.yml"
# opt= {'weights': 'cascade_rcnn_cls_aware_r200_vd_fpn_dcnv2_nonlocal_softnms'}
#
#
# '''This code contains of object detection'''
# cfg = load_config(config_file)
# merge_config(opt)
# check_config(cfg)
# # check if set use_gpu=True in paddlepaddle cpu version
# check_gpu(cfg.use_gpu)
# # check if paddlepaddle version is satisfied
# check_version()
#
# main_arch = cfg.architecture
# place = fluid.CUDAPlace(0) if cfg.use_gpu else fluid.CPUPlace()
# exe = fluid.Executor(place)
#
# model = create(main_arch)
#
# startup_prog = fluid.Program()
# infer_prog = fluid.Program()
# with fluid.program_guard(infer_prog, startup_prog):
#     with fluid.unique_name.guard():
#         inputs_def = cfg['TestReader']['inputs_def']
#         inputs_def['iterable'] = True
#         feed_vars, loader = model.build_inputs(**inputs_def)
#         test_fetches = model.test(feed_vars)
# infer_prog = infer_prog.clone(True)
# exe.run(startup_prog)
# if cfg.weights:
#     checkpoint.load_params(exe, infer_prog, cfg.weights)
#
# # parse infer fetches
# assert cfg.metric in ['COCO', 'VOC', 'OID', 'WIDERFACE'], \
#     "unknown metric type {}".format(cfg.metric)
# extra_keys = []
# if cfg['metric'] in ['COCO', 'OID']:
#     extra_keys = ['im_info', 'im_id', 'im_shape']
# if cfg['metric'] == 'VOC' or cfg['metric'] == 'WIDERFACE':
#     extra_keys = ['im_id', 'im_shape']
# keys, values, _ = parse_fetches(test_fetches, infer_prog, extra_keys)
#
# # parse dataset category
# if cfg.metric == 'COCO':
#     from ppdet.utils.coco_eval import bbox2out, mask2out, get_category_info
# if cfg.metric == 'OID':
#     from ppdet.utils.oid_eval import bbox2out, get_category_info
# if cfg.metric == "VOC":
#     from ppdet.utils.voc_eval import bbox2out, get_category_info
# if cfg.metric == "WIDERFACE":
#     from ppdet.utils.widerface_eval_utils import bbox2out, lmk2out, get_category_info
#
#
# def get_save_image_name(output_dir, image_path):
#     """
#     Get save image name from source image path.
#     """
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#     image_name = os.path.split(image_path)[-1]
#     name, ext = os.path.splitext(image_name)
#     return os.path.join(output_dir, "{}".format(name)) + ext
#
#
# def get_test_images(infer_dir, infer_img):
#     """
#     Get image path list in TEST mode
#     """
#     assert infer_img is not None or infer_dir is not None, \
#         "--infer_img or --infer_dir should be set"
#     assert infer_img is None or os.path.isfile(infer_img), \
#         "{} is not a file".format(infer_img)
#     assert infer_dir is None or os.path.isdir(infer_dir), \
#         "{} is not a directory".format(infer_dir)
#
#     # infer_img has a higher priority
#     if infer_img and os.path.isfile(infer_img):
#         return [infer_img]
#
#     images = set()
#     infer_dir = os.path.abspath(infer_dir)
#     assert os.path.isdir(infer_dir), \
#         "infer_dir {} is not a directory".format(infer_dir)
#     exts = ['jpg', 'jpeg', 'png', 'bmp']
#     exts += [ext.upper() for ext in exts]
#     for ext in exts:
#         images.update(glob.glob('{}/*.{}'.format(infer_dir, ext)))
#     images = list(images)
#
#     assert len(images) > 0, "no image found in {}".format(infer_dir)
#
#     return images
#
#
# '''
# Main predict code which takes file_name in the format of
# file_name = "uploads/" + f.filename
# '''
#
from init import ERR_LOGGER
import requests
import os
import json
def object_api(file_name):


    with open(file_name, 'rb') as f:
        read_data = f.read()
    files = {
        'file': read_data,
    }
    response = requests.post('http://api:5000/upload/', files=files)
    data = response.content.decode()
    data = json.loads(data)
    print(data)
    return data

def predict(file_name):
    try:
        objects = object_api(file_name)
        objects = ' '.join(captions)
        os.remove(file_name)
        return objects
    except Exception as e:
        print(f"{e} Exception in predict")
        ERR_LOGGER(f"{e} ERROR In predict")
        return ""