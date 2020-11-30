from django.contrib import admin
from django.urls import path,include

from . import views

app_name = "main"

urlpatterns = [
    path("",views.index , name="index_url"),
    path("handuploadapi/",views.handuploadapi ,name="handuploadapi_url"),

]
