# !/usr/bin/python


# {
#   "objects": [
#     "bottle",
#     "person"
#   ],
#   "score": [
#     0.6211097240447998,
#     0.42280933260917664
#   ]
# }
from __future__ import absolute_import, division, print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import glob
from paddle import fluid
from ppdet.core.workspace import load_config, merge_config, create
from ppdet.utils.eval_utils import parse_fetches
from ppdet.utils.check import check_gpu, check_version, check_config
import ppdet.utils.checkpoint as checkpoint
from ppdet.data.reader import create_reader
import logging
import json
from kafka import KafkaConsumer
from kafka import  KafkaProducer
from json import loads
from base64 import decodestring
import base64
from pathlib import Path
from dotenv import load_dotenv
import os
import uuid
load_dotenv()

'''This code contains the kafka initialization'''

TOPIC = "COCO_DATASET"

KAFKA_HOSTNAME = os.getenv("KAFKA_HOSTNAME")
KAFKA_PORT = os.getenv("KAFKA_PORT")

RECEIVE_TOPIC = 'COCO_DATASET'
SEND_TOPIC_FULL = "IMAGE_RESULTS"
SEND_TOPIC_TEXT = "TEXT"
print("kafka : "+KAFKA_HOSTNAME+':'+KAFKA_PORT)

import os
import numpy as np

'''Change this 2 lines in every object detection'''
config_file = "configs/dcn/cascade_rcnn_cls_aware_r200_vd_fpn_dcnv2_nonlocal_softnms.yml"
opt= {'weights': 'cascade_rcnn_cls_aware_r200_vd_fpn_dcnv2_nonlocal_softnms'}

'''This code contains of Kafka precode'''
FORMAT = '%(asctime)s-%(levelname)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)
consumer_easyocr = KafkaConsumer(
    RECEIVE_TOPIC,
    bootstrap_servers=[KAFKA_HOSTNAME+':'+KAFKA_PORT],
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="my-group",
    value_deserializer=lambda x: loads(x.decode("utf-8")),
)

# For Sending processed img data further 
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_HOSTNAME+':'+KAFKA_PORT],
    value_serializer=lambda x: json.dumps(x).encode("utf-8"),
)




'''This code contains of object detection'''
cfg = load_config(config_file)
merge_config(opt)
check_config(cfg)
# check if set use_gpu=True in paddlepaddle cpu version
check_gpu(cfg.use_gpu)
# check if paddlepaddle version is satisfied
check_version()

main_arch = cfg.architecture
place = fluid.CUDAPlace(0) if cfg.use_gpu else fluid.CPUPlace()
exe = fluid.Executor(place)

model = create(main_arch)

startup_prog = fluid.Program()
infer_prog = fluid.Program()
with fluid.program_guard(infer_prog, startup_prog):
    with fluid.unique_name.guard():
        inputs_def = cfg['TestReader']['inputs_def']
        inputs_def['iterable'] = True
        feed_vars, loader = model.build_inputs(**inputs_def)
        test_fetches = model.test(feed_vars)
infer_prog = infer_prog.clone(True)
exe.run(startup_prog)
if cfg.weights:
    checkpoint.load_params(exe, infer_prog, cfg.weights)

# parse infer fetches
assert cfg.metric in ['COCO', 'VOC', 'OID', 'WIDERFACE'], \
        "unknown metric type {}".format(cfg.metric)
extra_keys = []
if cfg['metric'] in ['COCO', 'OID']:
    extra_keys = ['im_info', 'im_id', 'im_shape']
if cfg['metric'] == 'VOC' or cfg['metric'] == 'WIDERFACE':
    extra_keys = ['im_id', 'im_shape']
keys, values, _ = parse_fetches(test_fetches, infer_prog, extra_keys)

# parse dataset category
if cfg.metric == 'COCO':
    from ppdet.utils.coco_eval import bbox2out, mask2out, get_category_info
if cfg.metric == 'OID':
    from ppdet.utils.oid_eval import bbox2out, get_category_info
if cfg.metric == "VOC":
    from ppdet.utils.voc_eval import bbox2out, get_category_info
if cfg.metric == "WIDERFACE":
    from ppdet.utils.widerface_eval_utils import bbox2out, lmk2out, get_category_info

def get_save_image_name(output_dir, image_path):
    """
    Get save image name from source image path.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    image_name = os.path.split(image_path)[-1]
    name, ext = os.path.splitext(image_name)
    return os.path.join(output_dir, "{}".format(name)) + ext


def get_test_images(infer_dir, infer_img):
    """
    Get image path list in TEST mode
    """
    assert infer_img is not None or infer_dir is not None, \
        "--infer_img or --infer_dir should be set"
    assert infer_img is None or os.path.isfile(infer_img), \
            "{} is not a file".format(infer_img)
    assert infer_dir is None or os.path.isdir(infer_dir), \
            "{} is not a directory".format(infer_dir)

    # infer_img has a higher priority
    if infer_img and os.path.isfile(infer_img):
        return [infer_img]

    images = set()
    infer_dir = os.path.abspath(infer_dir)
    assert os.path.isdir(infer_dir), \
        "infer_dir {} is not a directory".format(infer_dir)
    exts = ['jpg', 'jpeg', 'png', 'bmp']
    exts += [ext.upper() for ext in exts]
    for ext in exts:
        images.update(glob.glob('{}/*.{}'.format(infer_dir, ext)))
    images = list(images)

    assert len(images) > 0, "no image found in {}".format(infer_dir)
    logger.info("Found {} inference images in total.".format(len(images)))

    return images





'''
Main predict code which takes file_name in the format of 
file_name = "uploads/" + f.filename

'''
def predict(file_name):
    # args = upload_parser.parse_args()
    # f = args['file']
    # f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
    # file_name = "uploads/" + f.filename

    dataset = cfg.TestReader['dataset']
    infer_dir = "workspace"
    infer_img = file_name
    test_images = get_test_images(infer_dir, infer_img)
    dataset.set_images(test_images)
    reader = create_reader(cfg.TestReader, devices_num=1)
    loader.set_sample_list_generator(reader, place)
    anno_file = dataset.get_anno()
    with_background = dataset.with_background
    use_default_label = dataset.use_default_label

    clsid2catid, catid2name = get_category_info(anno_file, with_background,
                                                use_default_label)

    # whether output bbox is normalized in model output layer
    is_bbox_normalized = False
    if hasattr(model, 'is_bbox_normalized') and \
            callable(model.is_bbox_normalized):
        is_bbox_normalized = model.is_bbox_normalized()

    imid2path = dataset.get_imid2path()
    for iter_id, data in enumerate(loader()):
        outs = exe.run(infer_prog,
                        feed=data,
                        fetch_list=values,
                        return_numpy=False)
        res = {
            k: (np.array(v), v.recursive_sequence_lengths())
            for k, v in zip(keys, outs)
        }
        logger.info('Infer iter {}'.format(iter_id))
        if 'TTFNet' in cfg.architecture:
            res['bbox'][1].append([len(res['bbox'][0])])

        bbox_results = None
        mask_results = None
        lmk_results = None
        if 'bbox' in res:
            bbox_results = bbox2out([res], clsid2catid, is_bbox_normalized)
        if 'mask' in res:
            mask_results = mask2out([res], clsid2catid,
                                    model.mask_head.resolution)
        if 'landmark' in res:
            lmk_results = lmk2out([res], is_bbox_normalized)

        # visualize result
    im_ids = res['im_id'][0]
    objects = []
    scores = []
    for dt in np.array(bbox_results):

        catid, bbox, score = dt['category_id'], dt['bbox'], dt['score']
        if score > 0.1:
            if str(catid2name[catid]) in objects:
                pass
            else:
                objects.append(str(catid2name[catid]))
                scores.append(score)
    response_dict = {
        "objects": objects,
        "score": scores
    }
    os.remove(file_name)
    return response_dict
# if __name__ == '__main__':
#    app.run(debug=True)

if __name__ == "__main__":

    for message in consumer_easyocr:
        print('xxx--- inside open images consumer---xxx')
        print(KAFKA_HOSTNAME+':'+KAFKA_PORT)


        message = message.value
        print("MESSAGE RECEIVED consumer_COCODATASET: ")
        image_id = message['image_id']
        # data = message['data']

        # data = base64.b64decode(data.encode("ascii"))

    # '''TODO: To call the predict function and pass the requried file path'''

        # folder_path = "images/PP_YOLO/"
        # Path(folder_path).mkdir(parents=True, exist_ok=True)

        data = message['data']
        file_name= str(uuid.uuid4()) + ".jpg"
        with open(file_name, "wb") as fh:
            fh.write(base64.b64decode(data.encode("ascii")))

        response_dict=predict(file_name)
        '''
        From here the sending process begins
        '''
        full_res = {
            'image_id': image_id
        }

        text_res = {
            'image_id': image_id
        }

        # text = []
        # coords = []
        # for idx, prediction in enumerate(predictions):
        #     cords, word, confidence = prediction
        #     text.append(word)
        #     coords.append(cords)
            
        full_res["data"] = response_dict
        text_res["data"] = response_dict['objects']
        print(text_res)

        # sending full and text res(without cordinates or probability) to kafka
        producer.send(SEND_TOPIC_FULL, value=json.dumps(full_res))
        producer.send(SEND_TOPIC_TEXT, value=json.dumps(text_res))

        producer.flush()
