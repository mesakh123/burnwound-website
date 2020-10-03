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
                newdoc.save()
                newdoc.file_location = str(newdoc).split("website")[1].replace("ori",'resized')
                newdoc.save()
                image_ids.append(newdoc.id)
            else:
                newdoc = HandDocument(hand_docfile_ori = f_ori,hand_docfile_resized=f_resized)
                newdoc.save()
                newdoc.file_location = str(newdoc).split("website")[1].replace("ori",'resized')
                newdoc.save()
                image_ids.append(newdoc.id)
            file_name =str(newdoc)
            base64_cookie.append("\media"+file_name.split("media")[1].replace("ori",'resized'))
        else:
            if types=="burn":
                id = BurnDocument.objects.get(file_location=f).id
            else:
                id = HandDocument.objects.get(file_location=f).id
            image_ids.append(id)
            base64_cookie.append(f)

    return base64_cookie,image_ids


def predict_process(image_ids,types='burn'):
    image_urls = []
    for id in image_ids:
        if types=='burn':
            location = BurnDocument.objects.filter(pk=id).first()
            predict_image_in_background(location.id,types)
        else:
            location = HandDocument.objects.filter(pk=id).first()
            predict_image_in_background(location.id,types)
        image_urls.append(location.id)
    return image_urls


def burnupload(request):
    burn_image_session = []
    image_ids = []
    image_urls = []
    if(request.method == "POST"):
        if len(request.POST.getlist("images")) is 0:
            message="File can't be empty"
            return HttpResponseRedirect(reverse("demo:burnupload_url"))
        burn64_sess,image_ids =  upload_process(request.POST.getlist("images"),"burn")
        if "burn_image_session" not in request.session or len(burn64_sess)!=0:
            request.session["burn_image_session"] = burn64_sess
            request.session["burn_image_ids"] = image_ids
        request.session['form-burn-submitted'] = True
    else:
        if "burn_image_session" in request.session:
            burn_image_session = request.session.get("burn_image_session")
        if 'burn_image_ids' in request.session and "burn_image_session" in request.session:
            image_ids = request.session.get("burn_image_ids",None)
    if len(image_ids)!=0 or image_ids is not None:
        image_urls = predict_process(image_ids,'burn')
    return render(request, "demo/burnupload.html", locals())

def handupload(request):
    if 'form-burn-submitted' not in request.session:
        return HttpResponseRedirect(reverse("demo:burnupload_url"))
    hand_image_session = []
    image_ids = []
    if(request.method == "POST"):
        if len(request.POST.getlist("images")) is 0:
            message="File can't be empty"
        hand64_sess,image_ids =  upload_process(request.POST.getlist("images"),"hand")
        if len(hand64_sess)!=0:
            request.session["hand_image_session"] = hand64_sess
            request.session["hand_image_ids"] = image_ids
        request.session['form-hand-submitted'] = True
    else:
        if "hand_image_session" in request.session  and request.session['hand_image_session'] is not None :
            hand_image_session = request.session.get("hand_image_session")
        if 'hand_image_ids' in request.session and "hand_image_session" in request.session:
            image_ids = request.session.get("hand_image_ids",None)
    if image_ids is not None :
        image_urls = predict_process(image_ids,'palm')
    return render(request, "demo/handupload.html", locals())


def result(request):

    if 'form-patient-submitted' in request.session and 'form-burn-submitted' in request.session and 'form-hand-submitted' in request.session:
        data = request.session.get("data",False)
        if data:
            patientData = PatientData(
                name = data['name'],
                patient_id = data['patientid'],
                age = int(data['age']) if data['age'] is not '' else 1,
                sex = data['gender'],
                height= float(data['height']) if data['height'] is not '' else 100.0,
                weight = float(data['weight']) if data['weight'] is not '' else 2.0,
                burn_type = data['typeoption'],
                comments = data['comments']

            )
            patientData.save()
            predictResult = PredictResult()

            if "burn_image_session" in request.session:
                burn_image_session = [f.replace("burn",'predict\\burn') for f in request.session.get("burn_image_session")]
            if "hand_image_session" in request.session:
                hand_image_session = [f.replace("hand",'predict\\hand') for f in request.session.get("hand_image_session")]
            if "burn_image_ids" in request.session:
                burn_image_ids = request.session.get("burn_image_ids")
            if "hand_image_ids" in request.session:
                hand_image_ids = request.session.get("hand_image_ids")

            predictResult.result_code = str(hand_image_session[0]).rsplit("\\")[-1].split(".")[0]
            predictResult.save()
            hand_dict = {}
            burn_dict = {}
            while True:
                flag = True
                i = 0
                for id in burn_image_ids:
                    obj = None
                    try:
                        obj = BurnDocument.objects.get(pk=id)
                    except:
                        pass
                    if obj is not None:
                        if obj.predicted is False:
                            flag=False
                        else:
                            if int(obj.burn_pixel)!=0:
                                burn_dict[i]=int(obj.burn_pixel)
                                i+=1
                            obj.burn_result = predictResult
                            obj.save()
                time.sleep(1)

                i=0
                for id in hand_image_ids:
                    obj = None
                    try:
                        obj = HandDocument.objects.get(pk=id)
                    except:
                        pass
                    if obj is not None:
                        if obj.predicted is False:
                            flag=False
                        else:
                            if int(obj.hand_pixel)!=0:
                                hand_dict[i]=int(obj.hand_pixel)
                                i+=1
                            obj.hand_result = predictResult
                            obj.save()
                if flag is True:
                    break


            hand_total = 0
            burn_total = 0
            for v in hand_dict.values():
                hand_total+=v
            for v in burn_dict.values():
                burn_total+=v
            if hand_total!=0 and burn_total!=0:
                tbsa_result = burn_total*0.8/hand_total
                predictResult.predict_tbsa = tbsa_result
                predictResult.save()
            else:
                tbsa_result = False
    else:
        return HttpResponseRedirect(reverse("demo:burnupload_url"))
    try:
        for key in list(request.session.keys()):
            del request.session[key]
    except:
        pass

    return render(request, "demo/result.html", locals())
