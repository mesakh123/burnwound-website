<<<<<<< HEAD
from django.shortcuts import render

# Create your views here.
def index(request):
=======
from django.shortcuts import render,redirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse
import imghdr
from .models import HandDocument,BurnDocument,PatientData
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
        return HttpResponseRedirect('/')
    if request.method == "POST":
        if 'cleardata' in request.POST:
            try :
                del request.session['data']
                #del request.session['burn_image_session']
            except:
                pass
            return HttpResponseRedirect(reverse("main:inputdata_url"))
        else :
            if 'data' in request.session:
                del request.session['data']
            data = {}
            name = request.POST.get('name', '')
            data['name'] = name

            patientid = request.POST.get('patientid', '')
            data['patientid'] = patientid

            age = request.POST.get('age', '')
            print("Age : ",age)
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
            print(data)
            request.session['form-patient-submitted'] = True
            return HttpResponseRedirect(reverse("main:result_url"))

    if 'data' in request.session:
        print(request.session['data'])
        data = request.session['data']
    #del request.session['data']
    return render(request, "main/inputdata.html", locals())

def upload_process(files,types="burn"):
    """
    Process images from base64 to numpy files, then resize to 512x512, then upload to database
    (because of our model XD)
    files : list of base64 Images.
    types : based on different types, upload to different database
    """
    base64_cookie = []
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
            f = File(fileTemp, name=filenameRe+"-ori.png")
            if types=="burn":
                newdoc = BurnDocument(burn_docfile = f)
                newdoc.save()
            else:
                newdoc = HandDocument(hand_docfile = f)
                newdoc.save()
            file_name =str(newdoc)
            base64_cookie.append("\media"+file_name.split("media")[1].replace("-ori",""))
            file_name = file_name.replace("-ori","")
            import time
            time.sleep(1)
            cv2.imwrite(file_name,image_np[...,::-1])

        else:
            base64_cookie.append(f)

    return base64_cookie


def burnupload(request):
    burn_image_session = []

    if(request.method == "POST"):
        if len(request.POST.getlist("images")) is 0:
            message="File can't be empty"
            return render(request,"main/burnupload.html", locals())

        burn64_sess =  upload_process(request.POST.getlist("images"),"burn")
        if "burn_image_session" not in request.session or len(burn64_sess)!=0:
            request.session["burn_image_session"] = burn64_sess
        request.session['form-burn-submitted'] = True
    if "burn_image_session" in request.session:
        burn_image_session = request.session.get("burn_image_session")
    return render(request, "main/burnupload.html", locals())

def handupload(request):
    if 'form-burn-submitted' not in request.session:
        return HttpResponseRedirect("/")
    hand_image_session = []
    if(request.method == "POST"):
        if len(request.POST.getlist("images")) is 0:
            message="File can't be empty"
            return render(request,"main/handupload.html", locals())
        hand64_sess =  upload_process(request.POST.getlist("images"),"hand")
        if "hand_image_session" not in request.session or len(hand64_sess)!=0:
            request.session["hand_image_session"] = hand64_sess
        request.session['form-hand-submitted'] = True
    else:
        if "hand_image_session" in request.session:
            hand_image_session = request.session.get("hand_image_session")
    return render(request, "main/handupload.html", locals())


def result(request):

    if 'form-patient-submitted' in request.session and 'form-burn-submitted' in request.session and 'form-hand-submitted' in request.session:
        data = request.session.get("data",False)
        if data:
            for k in data.keys():
                print(k)
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
            if "burn_image_session" in request.session:
                burn_image_session = request.session.get("burn_image_session")
            if "hand_image_session" in request.session:
                hand_image_session = request.session.get("hand_image_session")

    else:
        return HttpResponseRedirect('/')
    try:
        for key in list(request.session.keys()):
            del request.session[key]
    except:
        pass
>>>>>>> e281625346f12ddae273a486a5ef4fea1ca65dda

    return render(request,"main/index.html",locals())
