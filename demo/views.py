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
from django.contrib import messages
from website.settings import PLATFORMTYPE
from .grpc_request import predict_image_in_background
from .views_utils import *
from django.http import JsonResponse
from io import StringIO
from django.core.files.base import ContentFile
import csv
from website import settings
from django.core.files import File
def burnupload(request):
    burn_image_session = []
    image_ids = []
    image_urls = []

    if(request.method == "POST"):
        if len(request.POST.getlist("images")) is 0:
            message="File can't be empty"
            messages.error(request,message)
            return HttpResponseRedirect(reverse("demo:burnupload_url"))
        user_calculated_tbsa = request.POST.getlist("user_calculated_tbsa")
        burn64_sess,image_ids =  upload_process(request.POST.getlist("images"),"burn",user_calculated_tbsa)
        if "burn_image_session" not in request.session or len(burn64_sess)!=0:
            request.session["burn_image_session"] = burn64_sess
            request.session["burn_image_ids"] = image_ids
        request.session['form-burn-submitted'] = True
        if len(image_ids)!=0 or image_ids is not None:
            image_urls = predict_process(image_ids,'burn')
    else:
        if "burn_image_session" in request.session:
            burn_image_session = request.session.get("burn_image_session")
        if 'burn_image_ids' in request.session and "burn_image_session" in request.session:
            image_ids = request.session.get("burn_image_ids",None)

    return render(request, "demo/burnupload.html", locals())

def handupload(request):
    if 'form-burn-submitted' not in request.session:
        return HttpResponseRedirect(reverse("demo:burnupload_url"))
    hand_image_session = []
    image_ids = []
    if(request.method == "POST"):
        if len(request.POST.getlist("images")) is 0:
            message="File can't be empty"
        hand64_sess,image_ids =  upload_process(request.POST.getlist("images"),"hand",[0])
        if len(hand64_sess)!=0:
            request.session["hand_image_session"] = hand64_sess
            request.session["hand_image_ids"] = image_ids
        request.session['form-hand-submitted'] = True
        if image_ids is not None :
            image_urls = predict_process(image_ids,'palm')
    else:
        if "hand_image_session" in request.session  and request.session['hand_image_session'] is not None :
            hand_image_session = request.session.get("hand_image_session")
        if 'hand_image_ids' in request.session and "hand_image_session" in request.session:
            image_ids = request.session.get("hand_image_ids",None)

    return render(request, "demo/handupload.html", locals())

def result(request):
    burn_image_dict = {}
    hand_image_dict = {}
    result_code = ""
    predictResult = None
    manual_tbsa = None
    patient_id = ""
    weight = 0.0
    if 'form-patient-submitted' in request.session and 'form-burn-submitted' in request.session and 'form-hand-submitted' in request.session:
        data = request.session.get("data",False)
        print("Test : ",)
        if data:
            patient_id = data['patientid'] if data['patientid'] is not '' else ''
            patientData = PatientData(
                name = data['name'] if data['name'] is not '' else '',
                patient_id = patient_id,
                age = int(data['age']) if data['age'] is not '' else 1,
                sex = data['gender'] if data['gender'] is not '' else '',
                height= float(data['height']) if data['height'] is not '' else 100.0,
                weight = float(data['weight']) if data['weight'] is not '' else 2.0,
                burn_type = data['typeoption'],
                comments = data['comments']

            )
            weight = float(data['weight']) if data['weight'] is not '' else 2.0
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
                predictResult.result_code = str(hand_image_session[0]).rsplit("\\")[-1].split(".")[0].split("-")[0]

            else:
                predictResult.result_code = str(hand_image_session[0]).rsplit("/")[-1].split(".")[0].split("-")[0]
            predictResult.patient=patientData
            predictResult.save()
            result_code = predictResult.result_code
            hand_pixel_dict = {};burn_pixel_dict = {};burn_image_dict = {};hand_image_dict = {}
            while True:
                flag = True
                time.sleep(1)
                burn_flag, burn_pixel_dict,burn_image_dict,manual_tbsa = loading_database(burn_image_ids,'burn',predictResult)
                time.sleep(2)
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
                predictResult.predict_tbsa_ai = tbsa_result
            else:
                tbsa_result = False
            ai_after_eight_hours = 0;ai_after_sixteen_hours=0;manual_after_eight_hours=0;manual_after_sixteen_hours=0;
            if tbsa_result and data['weight']!='':
                ai_after_eight_hours = (burn_total/hand_total)*float(data['weight'])*0.125
                ai_after_sixteen_hours = (burn_total/hand_total)*float(data['weight'])*0.0625
                predictResult.ai_after_eight_hours = float(ai_after_eight_hours)
                predictResult.ai_after_sixteen_hours = float(ai_after_sixteen_hours)
            if tbsa_result and data['weight']!='' and manual_tbsa:
                manual_after_eight_hours = manual_tbsa*float(data['weight'])*0.25
                manual_after_sixteen_hours = manual_tbsa*float(data['weight'])*0.125
                predictResult.manual_after_eight_hours = float(manual_after_eight_hours)
                predictResult.manual_after_sixteen_hours = float(manual_after_sixteen_hours)

            predictResult.save()
    else:
        #print("do nothing")
        return HttpResponseRedirect(reverse("demo:burnupload_url"))

    try:
        for key in list(request.session.keys()):
            del request.session[key]
    except:
        pass
    if predictResult:
        request.session["feedback"] = predictResult.id
    if manual_tbsa:
        request.session["manual_tbsa"] = manual_tbsa
    return render(request, "demo/result.html", locals())

def feedbacksubmit(request):
    if request.method=="POST" and request.is_ajax:

        result_code = request.POST.get("result_code",None)
        feedback_tbsa = request.POST.get("feedback_tbsa",None)
        feedback_8 = request.POST.get("feedback_8",None)
        feedback_16 = request.POST.get("feedback_16",None)
        manual_tbsa = None
        if "manual_tbsa" in request.session:
            manual_tbsa = request.session["manual_tbsa"]

        if result_code and feedback_tbsa and feedback_8 and feedback_16 :
            try:
                predictResult = PredictResult.objects.get(result_code=result_code)
            except PredictResult.DoesNotExist:
                predictResult =None
            if predictResult:
                patient = predictResult.patient

                list_left = ["預測ID","姓名","性別","身分證","年齡","身高","體重","燙傷類別","AI判斷TBSA","AI判斷前8小時點","AI判斷後16小時點",
                "使用者手動輸入TBSA", "使用者手動輸入TBSA前8小時點","使用者手動輸入TBSA後16小時點","使用者回饋TBSA","使用者回饋TBSA前8小時點","使用者回饋TBSA前16小時點",]
                list_right = [result_code,patient.name,patient.sex,patient.id,patient.age,patient.height,patient.weight,patient.burn_type,
                    predictResult.predict_tbsa_ai,predictResult.ai_after_eight_hours,predictResult.ai_after_sixteen_hours,
                    manual_tbsa,predictResult.manual_after_eight_hours,predictResult.manual_after_sixteen_hours,feedback_tbsa,feedback_8,feedback_16]
                predictResult.feedback_tbsa =feedback_tbsa
                predictResult.feedback_after_eight_hours = feedback_8
                predictResult.feedback_after_sixteen_hours = feedback_16

                rows = zip(list_left,list_right)

                path = os.path.join(settings.MEDIA_ROOT, 'documents', 'predict', 'file',result_code+'.csv')
                if os.path.exists(path):
                    os.remove(path)
                path = result_code+".csv"

                csv_buffer = StringIO()
                csv_writer = csv.writer(csv_buffer)
                for row in rows:
                    csv_writer.writerow(row)
                csv_file = ContentFile(csv_buffer.getvalue().encode('utf-8'))

                predictResult.predict_file.save(path,csv_file)
                predictResult.save()
                response = {
                     'msg':'Your form has been submitted successfully', # response message
                     'file_url': "/media/"+str(predictResult.predict_file),
                }
                return JsonResponse(response) # return response as JSON
    response = {
         'msg':'Your form has been failed to submit' # response message
    }
    return JsonResponse(response) # return response as JSON
