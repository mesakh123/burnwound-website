from background_task import background
import time
import cv2
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
import numpy as np
from .mrcnn import visualize
from .models import HandDocument,BurnDocument,PatientData
from .burn_inferencing.saved_model_inference import detect_mask_single_image_using_grpc as burn_detect_mask
from .hand_inferencing.saved_model_inference import detect_mask_single_image_using_grpc as hand_detect_mask
@background(schedule=0)
def predict_image_in_background(id,types='burn'):
    if types=='burn':
        class_names = ['BG', 'burn']
        location= BurnDocument.objects.filter(pk=id).first()
    else:
        print("Predict hand started")
        class_names = ['BG','palm']
        location = HandDocument.objects.filter(pk=id).first()
    if location.predicted is False:
        folder , file_name = str(location).rsplit("\\",1)
        image = cv2.imread(str(location),1)[:,:,::-1]
        if types=='burn':
            result = burn_detect_mask(image)
            predict_image_field = location.burn_predict_docfile
        else:
            result = hand_detect_mask(image)
            predict_image_field = location.hand_predict_docfile

        if result is not None:
            predict_result = visualize.save_image(image, "test", result['rois'], result['mask'],
                        result['class'], result['scores'], class_names,scores_thresh=0.85)
            buffer = BytesIO()
            predict_result.save(fp=buffer,format='JPEG')
            pillow_image = ContentFile(buffer.getvalue())
            mask_area = np.reshape(result['mask'], (-1, result['mask'].shape[-1])).astype(np.float32).sum()

            if types=='burn':
                location.burn_pixel = mask_area
            else:
                location.hand_pixel = mask_area
            predict_image_field.save(file_name,InMemoryUploadedFile(
                    pillow_image,
                    None,
                    file_name,
                    'image/jpeg',
                    pillow_image.tell,
                    None
                )
            )
        location.predicted = True
        location.save()
    print("Predict success!")
"""    if types is 'burn':
        try:
            image = BurnDocument.objects.get(pk=id)
        except:
            image = 'empty'
        with open('output.txt','w') as f:
            f.write(str(image))
"""
