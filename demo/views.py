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
from .views_utils import *


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
    burn_image_dict = {}
    hand_image_dict = {}
    result_code = ""
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
            if "burn_image_ids" in request.session:
                burn_image_ids = request.session.get("burn_image_ids")
            if "hand_image_ids" in request.session:
                hand_image_ids = request.session.get("hand_image_ids")

            if "hand_image_session" in request.session:
                hand_image_session = request.session.get("hand_image_session")
            if "burn_image_session" in request.session:
                burn_image_session = request.session.get("burn_image_session")

            if PLATFORMTYPE is 'Windows' :
                predictResult.result_code = str(hand_image_session[0]).rsplit("\\")[-1].split(".")[0]

            else:
                predictResult.result_code = str(hand_image_session[0]).rsplit("/")[-1].split(".")[0]
            predictResult.save()
            result_code = predictResult.result_code.split("-")[0]
            hand_pixel_dict = {};burn_pixel_dict = {};burn_image_dict = {};hand_image_dict = {}
            while True:
                flag = True
                time.sleep(5)
                burn_flag, burn_pixel_dict,burn_image_dict = loading_database(burn_image_ids,'burn',predictResult)
                time.sleep(3)
                hand_flag, hand_pixel_dict,hand_image_dict = loading_database(hand_image_ids,'hand',predictResult)
                flag = burn_flag and hand_flag
                if len(burn_image_dict) and len(hand_image_dict):
                    if flag is True:
                        break

            hand_total = 0;burn_total = 0;
            for v in hand_pixel_dict.values():
                hand_total+=v
            for v in burn_pixel_dict.values():
                burn_total+=v
            if hand_total!=0 and burn_total!=0:
                tbsa_result = burn_total*0.5/hand_total
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
