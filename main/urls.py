from django.contrib import admin
from django.urls import path,include

from . import views

app_name = "main"

urlpatterns = [
<<<<<<< HEAD
    path("",views.index , name="index_url"),
=======
    path("",views.burnupload , name="burnupload_url"),
    path("result/",views.result , name="result_url"),
    path("inputdata/",views.inputdata, name="inputdata_url"),
    path("handupload/",views.handupload, name="handupload_url"),
>>>>>>> e281625346f12ddae273a486a5ef4fea1ca65dda
]
