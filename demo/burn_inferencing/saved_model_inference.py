import cv2, grpc
from tensorflow_serving.apis import prediction_service_pb2_grpc
from tensorflow_serving.apis import predict_pb2
import numpy as np
import tensorflow as tf
from . import saved_model_config
from .saved_model_preprocess import ForwardModel
import requests
import json
import skimage.io
import time
from .mrcnn import visualize
host = saved_model_config.ADDRESS
PORT_GRPC = saved_model_config.PORT_NO_GRPC
RESTAPI_URL = saved_model_config.REST_API_URL

channel = grpc.insecure_channel(str(host) + ':' + str(PORT_GRPC), options=[('grpc.max_receive_message_length', saved_model_config.GRPC_MAX_RECEIVE_MESSAGE_LENGTH)])

stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)


request = predict_pb2.PredictRequest()
request.model_spec.name = saved_model_config.MODEL_NAME
request.model_spec.signature_name = saved_model_config.SIGNATURE_NAME

model_config = saved_model_config.MY_INFERENCE_CONFIG
preprocess_obj = ForwardModel(model_config)


def detect_mask_single_image_using_grpc(image):
    images = np.expand_dims(image, axis=0)
    molded_images, image_metas, windows = preprocess_obj.mold_inputs(images)
    molded_images = molded_images.astype(np.float32)
    image_metas = image_metas.astype(np.float32)
    # Validate image sizes
    # All images in a batch MUST be of the same size
    image_shape = molded_images[0].shape
    for g in molded_images[1:]:
        assert g.shape == image_shape, \
            "After resizing, all images must have the same size. Check IMAGE_RESIZE_MODE and image sizes."

    # Anchors
    anchors = preprocess_obj.get_anchors(image_shape)
    anchors = np.broadcast_to(anchors, (molded_images.shape[0],) + anchors.shape)


    if int(tf.__version__[0]) >= 2 :
        request.inputs[saved_model_config.INPUT_IMAGE].CopyFrom(
            tf.make_tensor_proto(molded_images, shape=molded_images.shape))
        request.inputs[saved_model_config.INPUT_IMAGE_META].CopyFrom(
            tf.make_tensor_proto(image_metas, shape=image_metas.shape))
        request.inputs[saved_model_config.INPUT_ANCHORS].CopyFrom(
            tf.make_tensor_proto(anchors, shape=anchors.shape))
    else:
        request.inputs[saved_model_config.INPUT_IMAGE].CopyFrom(
            tf.contrib.util.make_tensor_proto(molded_images, shape=molded_images.shape))
        request.inputs[saved_model_config.INPUT_IMAGE_META].CopyFrom(
            tf.contrib.util.make_tensor_proto(image_metas, shape=image_metas.shape))
        request.inputs[saved_model_config.INPUT_ANCHORS].CopyFrom(
            tf.contrib.util.make_tensor_proto(anchors, shape=anchors.shape))

    try:
        result = stub.Predict(request,30)#(request,10.0)
    except:
        return None
    result_dict = preprocess_obj.result_to_dict(images, molded_images, windows, result)[0]
    return result_dict


def preprocess_image(input_images):
    anchor_list= []
    image_meta_list = []
    molded_image_list = []
    for image in input_images:
        images = np.expand_dims(image, axis=0)
        molded_images, image_metas, windows = preprocess_obj.mold_inputs(images)
        molded_images = molded_images.astype(np.float32)
        image_metas = image_metas.astype(np.float32)
        # Validate image sizes
        # All images in a batch MUST be of the same size
        image_shape = molded_images[0].shape
        for g in molded_images[1:]:
            assert g.shape == image_shape, \
                "After resizing, all images must have the same size. Check IMAGE_RESIZE_MODE and image sizes."

        # Anchors
        anchors = preprocess_obj.get_anchors(image_shape)
        anchors = np.broadcast_to(anchors, (molded_images.shape[0],) + anchors.shape)

        anchor_list.append(anchors[0])
        image_meta_list.append(image_metas[0])
        molded_image_list.append(molded_images[0])

    anchor_list = np.array(anchor_list)
    image_meta_list = np.array(image_meta_list)
    molded_image_list = np.array(molded_image_list)
    return anchor_list,image_meta_list,molded_image_list

def detect_mask_multiple_image_using_grpc(input_images):
    anchor_list,image_meta_list,molded_image_list = preprocess_image(input_images)

    request.inputs[saved_model_config.INPUT_IMAGE].CopyFrom(
        tf.contrib.util.make_tensor_proto(molded_image_list))
    request.inputs[saved_model_config.INPUT_IMAGE_META].CopyFrom(
        tf.contrib.util.make_tensor_proto(image_meta_list))
    request.inputs[saved_model_config.INPUT_ANCHORS].CopyFrom(
        tf.contrib.util.make_tensor_proto(anchor_list))

    result = stub.Predict(request,30.0)#(request,10.0)
    #result_dict = preprocess_obj.result_to_dict(images, molded_images, windows, result)[0]
    return result,anchor_list,image_meta_list,molded_image_list


def detect_mask_single_image_using_restapi(image):
    images = np.expand_dims(image, axis=0)

    molded_images, image_metas, windows = preprocess_obj.mold_inputs(images)

    molded_images = molded_images.astype(np.float32)

    image_shape = molded_images[0].shape

    for g in molded_images[1:]:
        assert g.shape == image_shape, \
            "After resizing, all images must have the same size. Check IMAGE_RESIZE_MODE and image sizes."

    anchors = preprocess_obj.get_anchors(image_shape)
    anchors = np.broadcast_to(anchors, (images.shape[0],) + anchors.shape)


    # response body format row wise.
    data = {'signature_name': saved_model_config.SIGNATURE_NAME,
            'instances': [{saved_model_config.INPUT_IMAGE: molded_images[0].tolist(),
                           saved_model_config.INPUT_IMAGE_META: image_metas[0].tolist(),
                           saved_model_config.INPUT_ANCHORS: anchors[0].tolist()}]}

    response = requests.post(RESTAPI_URL, data=json.dumps(data), headers={"content-type":"application/json"})
    result = json.loads(response.text)
    with open('data.txt','w') as f:
        json.dump(result,f)
    result = result['predictions'][0]

    result_dict = preprocess_obj.result_to_dict(images, molded_images, windows, result, is_restapi=True)[0]
    return result_dict



class_names = ['BG', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
               'bus', 'train', 'truck', 'boat', 'traffic light',
               'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
               'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
               'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
               'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
               'kite', 'baseball bat', 'baseball glove', 'skateboard',
               'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
               'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
               'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
               'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
               'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
               'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
               'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
               'teddy bear', 'hair drier', 'toothbrush']
class_names = ['BG', 'burn']
if __name__ == '__main__':
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', help='Path to Image', required=True)
    parser.add_argument('-t', '--type', help='Type of call [restapi, grpc]', default='restapi')
    args = vars(parser.parse_args())
    image_path = args['path']
    call_type = args['type']

    if not os.path.exists(image_path):
        print(image_path, " -- Does not exist")
        exit()

    image = cv2.imread(image_path,1)
    image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    #image = image[:,:,::-1]
    if image is None:
        print("Image path is not proper")
        exit()

    start_time = time.time()
    if call_type == 'restapi':
        result = detect_mask_single_image_using_restapi(image)
    else:
        result = detect_mask_single_image_using_grpc(image)

    visualize.save_image(image, "test", result['rois'], result['mask'],
        result['class'], result['scores'], class_names,scores_thresh=0.85)
    print("*" * 60)
    print("Score : ",result['scores'])
    print("Execution time : %s " % (time.time() - start_time))
    print("*" * 60)
