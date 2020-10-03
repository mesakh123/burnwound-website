from django.shortcuts import render,redirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse
import imghdr
from .models import HandDocument,BurnDocument,PatientData,PredictResult
from .forms import DocumentForm
import urllib.request as ulrequest
import base64
import io
from PIL import Image
from django.core.files import File
from django.core.files.uploadedfile import *
from django.core.files.temp import NamedTemporaryFile
import numpy as np
from .utils import resize_image
import cv2
import random
import string
import os
import shutil
import time
from website.settings import PLATFORMTYPE
from .grpc_request import predict_image_in_background


def get_random_string(length):
    """
    Generate 'length' length of random characters
    """
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

def inputdata(request):
    data = None
    if 'form-burn-submitted' not in request.session or 'form-hand-submitted' not in request.session:
        return HttpResponseRedirect(reverse("demo:burnupload_url"))
    if request.method == "POST":
        if 'cleardata' in request.POST:
            try :
                del request.session['data']
                #del request.session['burn_image_session']
            except:
                pass
            return HttpResponseRedirect(reverse("demo:inputdata_url"))
        else :
            if 'data' in request.session:
                del request.session['data']
            data = {}
            name = request.POST.get('name', '')
            data['name'] = name

            patientid = request.POST.get('patientid', '')
            data['patientid'] = patientid

            age = request.POST.get('age', '')
            data['age'] = age

            gender = request.POST.get('gender', '')
            data['gender'] = gender

            height = request.POST.get('height', '100.0')
            data['height'] = height

            weight = request.POST.get('weight', '3.0')
            data['weight'] = weight

            typeoption = request.POST.get('typeoption', '')
            data['typeoption'] = typeoption

            comments = request.POST.get('comments', '')
            data['comments'] = comments

            request.session['data'] =  data
            request.session['form-patient-submitted'] = True
            return HttpResponseRedirect(reverse("demo:result_url"))

    if 'data' in request.session:
        data = request.session['data']
    #del request.session['data']
    return render(request, "demo/inputdata.html", locals())

def upload_process(files,types="burn"):
    """
    Process images from base64 to numpy files, then resize to 512x512, then upload to database
    (because of our model XD)
    files : list of base64 Images.
    types : based on different types, upload to different database
    """
    base64_cookie = []
    image_ids = []
    for f in files:
        if len(f.split(';base64,'))>1:
            format, f = f.split(';base64,')
            f = base64.b64decode(f)
            image_np = Image.open(io.BytesIO(f))
            image_np = np.asarray(image_np)
            image_np, window, scale, padding, crop = resize_image(image_np,min_dim=512, max_dim=512)
            fileTemp = NamedTemporaryFile()
            fileTemp.write(f)
            filenameRe = get_random_string(15)
            f_ori = File(fileTemp, name=filenameRe+"-ori.png")
            f_resized = File(fileTemp, name=filenameRe+"-resized.png")
            if types=="burn":
                newdoc = BurnDocument(burn_docfile_ori = f_ori,burn_docfile_resized=f_resized)
            else:
                newdoc = HandDocument(hand_docfile_ori = f_ori,hand_docfile_resized=f_resized)
            newdoc.save()
            newdoc.file_location = str(newdoc).split("website")[1].replace("ori",'resized')
            newdoc.save()
            image_ids.append(newdoc.id)
            file_name =str(newdoc)
            if PLATFORMTYPE is 'Windows':
                base64_cookie.append("\media"+file_name.split("media")[1].replace("ori",'resized'))
            else:
                base64_cookie.append("/media"+file_name.split("media")[1].replace("ori",'resized'))
        else:
            if types=="burn":
                id = BurnDocument.objects.get(file_location=f).id
            else:
                id = HandDocument.objects.get(file_location=f).id
            image_ids.append(id)
            base64_cookie.append(f)

    return base64_cookie,image_ids


def predict_process(image_ids,types='burn'):
    for id in image_ids:
        if types=='burn':
            location = BurnDocument.objects.filter(pk=id).first()
        else:
            location = HandDocument.objects.filter(pk=id).first()
        if location.process_predict is False:
            location.process_predict = True
            location.save()
            predict_image_in_background(location.id,types)

def loading_database(image_ids,types='burn',predictResult=None):
    pixel_dict = {}
    image_dict = {}
    flag=True
    i = 0
    for id in image_ids:
        obj = None
        try:
            if types is 'burn':
                obj = BurnDocument.objects.get(pk=id)
            else:
                obj = HandDocument.objects.get(pk=id)
        except:
            pass
        if obj is not None:
            if obj.predicted:
                if types=='burn':
                    if int(obj.burn_pixel)!=0:
                        pixel_dict[i]=int(obj.burn_pixel)
                        image_dict[id] = str(obj.burn_predict_docfile)
                        i+=1
                    else:
                        image_dict[id] = str(obj.burn_docfile_resized)
                    obj.burn_result = predictResult
                else:
                    if int(obj.hand_pixel)!=0:
                        pixel_dict[i]=int(obj.hand_pixel)
                        image_dict[id] = str(obj.hand_predict_docfile)
                        i+=1
                    else:
                        image_dict[id] = str(obj.hand_docfile_resized)

                    obj.hand_result = predictResult
                obj.save()
            else:
                if obj.process_predict is False:
                    flag=False
    return flag,pixel_dict,image_dict
