
from django.shortcuts import render,redirect,reverse
from django.contrib import messages
from demo.views_utils import *
# Create your views here.
def index(request):
    return render(request,"main/index.html",locals())

def handuploadapi(request):
    if request.method=="GET":
        return render(request,"main/handupload.html",locals())
    if len(request.POST.getlist("images")) is 0:
        message="File can't be empty"
        messages.error(request, message)
        return render(request,"main/handupload.html",locals())
    flag=True
    try:
        print("HERE")
        hand64_sess,image_ids =  upload_process(request.POST.getlist("images"),"hand",[0])
    except:
        print("HERE2")
        flag=False
    if flag:
        messages.success(request, 'upload success')
    else:
        messages.error(request,"upload fail")
    return redirect(reverse("main:handuploadapi_url"))
